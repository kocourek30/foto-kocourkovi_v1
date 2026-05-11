from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import urlencode
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from apps.galleries.models import Gallery, GalleryStatus
from apps.orders.forms import OrderSubmitContactForm
from apps.orders.models import GalleryOrder, GalleryOrderItem, GalleryPrintOption, OrderStatus
from apps.orders.services import (
    add_item_to_cart,
    create_draft_order,
    get_draft_order,
    get_last_submitted_order,
    remove_item_from_cart,
    submit_order,
    update_item_quantity,
)
from apps.photos.models import Photo


def _get_accessible_gallery_or_404(token: str) -> Gallery:
    gallery = get_object_or_404(Gallery, token=token)
    if gallery.status != GalleryStatus.PUBLISHED:
        raise Http404("Galerie není dostupná.")
    if gallery.expires_at is not None and timezone.now() > gallery.expires_at:
        raise Http404("Galerie není dostupná.")
    return gallery


def _ensure_session_key(request) -> str:
    if not request.session.session_key:
        request.session.save()
    return request.session.session_key


def _render_cart_detail(request, gallery, session_key, token, contact_form=None, status=200):
    order = get_draft_order(gallery=gallery, session_key=session_key)
    submitted_order = get_last_submitted_order(gallery=gallery, session_key=session_key)
    active_order = order or submitted_order
    items = active_order.items.select_related("photo", "print_option").order_by("id") if active_order else []

    rows = []
    for item in items:
        thumb_url = reverse(
            "client-gallery-photo-thumbnail",
            kwargs={"token": token, "photo_id": item.photo_id},
        )
        rows.append(
            {
                "id": item.id,
                "photo_id": item.photo_id,
                "caption": item.photo.caption,
                "thumb_url": thumb_url,
                "print_label": item.print_option.label,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "subtotal": item.subtotal,
            }
        )

    if contact_form is None:
        contact_form = OrderSubmitContactForm(
            initial={
                "customer_email": order.customer_email if order else "",
                "customer_first_name": order.customer_first_name if order else "",
                "customer_last_name": order.customer_last_name if order else "",
            }
        )

    context = {
        "gallery": gallery,
        "order": active_order,
        "has_active_draft": bool(order),
        "submitted_exists": bool(submitted_order and not order),
        "items": rows,
        "items_count": active_order.items_count if active_order else 0,
        "total_price": active_order.total_price if active_order else 0,
        "contact_form": contact_form,
    }
    return render(request, "orders/cart_detail.html", context, status=status)


@require_GET
def cart_detail_view(request, token):
    gallery = _get_accessible_gallery_or_404(token)
    session_key = _ensure_session_key(request)
    return _render_cart_detail(request, gallery=gallery, session_key=session_key, token=token)


@require_POST
def cart_add_item_view(request, token):
    gallery = _get_accessible_gallery_or_404(token)
    session_key = _ensure_session_key(request)
    order = get_draft_order(gallery=gallery, session_key=session_key)
    if order is None:
        if get_last_submitted_order(gallery=gallery, session_key=session_key):
            messages.warning(
                request,
                "Objednávka už byla odeslaná. Pro novou objednávku začněte nový košík.",
            )
            return redirect("orders-cart-detail", token=token)
        order = create_draft_order(gallery=gallery, session_key=session_key)

    photo_id = request.POST.get("photo_id")
    print_option_id = request.POST.get("print_option_id")
    quantity_raw = request.POST.get("quantity", "1")
    try:
        quantity = int(quantity_raw)
    except (TypeError, ValueError):
        quantity = 0

    photo = get_object_or_404(Photo, id=photo_id, gallery=gallery, is_active=True)
    print_option = get_object_or_404(
        GalleryPrintOption,
        id=print_option_id,
        gallery=gallery,
        is_active=True,
    )

    try:
        add_item_to_cart(order=order, photo=photo, print_option=print_option, quantity=quantity)
    except ValidationError as exc:
        detail = "; ".join(exc.messages) if getattr(exc, "messages", None) else "Neplatná data."
        messages.error(request, f"Položku se nepodařilo přidat. {detail}")
    else:
        messages.success(
            request,
            f"Fotka #{photo.id} ({print_option.label}) byla přidána do košíku.",
        )
        gallery_url = reverse("client-gallery", kwargs={"token": token})
        query = urlencode({"added_photo_id": photo.id})
        return redirect(f"{gallery_url}?{query}")

    return redirect("client-gallery", token=token)


@require_POST
def cart_remove_item_view(request, token, item_id):
    gallery = _get_accessible_gallery_or_404(token)
    session_key = _ensure_session_key(request)
    order = get_draft_order(gallery=gallery, session_key=session_key)
    if order is None:
        messages.warning(
            request,
            "Rozpracovaný košík neexistuje.",
        )
        return redirect("orders-cart-detail", token=token)
    item = get_object_or_404(
        GalleryOrderItem.objects.select_related("order"),
        id=item_id,
        order__gallery=gallery,
        order__session_key=session_key,
        order__status=OrderStatus.DRAFT,
    )
    try:
        remove_item_from_cart(order=order, item=item)
    except ValidationError as exc:
        detail = "; ".join(exc.messages) if getattr(exc, "messages", None) else "Neplatná data."
        messages.error(request, f"Položku se nepodařilo odebrat. {detail}")
    else:
        messages.success(request, "Položka byla odebrána z košíku.")
    return redirect("orders-cart-detail", token=token)


@require_POST
def cart_update_item_quantity_view(request, token, item_id):
    gallery = _get_accessible_gallery_or_404(token)
    session_key = _ensure_session_key(request)
    order = get_draft_order(gallery=gallery, session_key=session_key)
    if order is None:
        messages.warning(request, "Rozpracovaný košík neexistuje.")
        return redirect("orders-cart-detail", token=token)

    item = get_object_or_404(
        GalleryOrderItem.objects.select_related("order", "photo"),
        id=item_id,
        order__gallery=gallery,
        order__session_key=session_key,
        order__status=OrderStatus.DRAFT,
    )

    action = request.POST.get("action", "set")
    quantity_raw = request.POST.get("quantity", str(item.quantity))
    try:
        quantity = int(quantity_raw)
    except (TypeError, ValueError):
        quantity = item.quantity

    if action == "increase":
        quantity = item.quantity + 1
    elif action == "decrease":
        quantity = item.quantity - 1

    try:
        update_item_quantity(order=order, item=item, quantity=quantity)
    except ValidationError as exc:
        detail = "; ".join(exc.messages) if getattr(exc, "messages", None) else "Neplatná data."
        messages.error(request, f"Počet se nepodařilo upravit. {detail}")
    else:
        messages.success(request, f"Počet u Fotka #{item.photo_id} byl aktualizován.")

    return redirect("orders-cart-detail", token=token)


@require_POST
def orders_cart_submit_view(request, token):
    gallery = _get_accessible_gallery_or_404(token)
    session_key = _ensure_session_key(request)
    order = get_draft_order(gallery=gallery, session_key=session_key)
    if order is None:
        messages.warning(request, "Rozpracovaná objednávka nebyla nalezena.")
        return redirect("orders-cart-detail", token=token)

    form = OrderSubmitContactForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Objednávku se nepodařilo odeslat. Zkontrolujte kontaktní údaje.")
        return _render_cart_detail(
            request,
            gallery=gallery,
            session_key=session_key,
            token=token,
            contact_form=form,
            status=400,
        )

    order.customer_email = form.cleaned_data["customer_email"]
    order.customer_first_name = form.cleaned_data["customer_first_name"]
    order.customer_last_name = form.cleaned_data["customer_last_name"]
    order.save(update_fields=["customer_email", "customer_first_name", "customer_last_name", "updated_at"])

    try:
        submit_order(order)
    except ValidationError as exc:
        detail = "; ".join(exc.messages) if getattr(exc, "messages", None) else "Neplatná data."
        messages.error(request, f"Objednávku se nepodařilo odeslat. {detail}")
        return redirect("orders-cart-detail", token=token)

    messages.success(request, "Objednávka byla úspěšně odeslána.")
    return redirect("orders-confirmation", token=token, public_id=order.public_id)


@require_GET
def orders_confirmation_view(request, token, public_id):
    gallery = _get_accessible_gallery_or_404(token)
    session_key = _ensure_session_key(request)
    order = get_object_or_404(
        GalleryOrder.objects.prefetch_related("items__photo", "items__print_option"),
        public_id=public_id,
        gallery=gallery,
        status=OrderStatus.SUBMITTED,
    )
    if order.session_key != session_key:
        raise Http404("Objednávka není dostupná.")

    rows = []
    for item in order.items.all().order_by("id"):
        rows.append(
            {
                "id": item.id,
                "photo_id": item.photo_id,
                "caption": item.photo.caption,
                "thumb_url": reverse(
                    "client-gallery-photo-thumbnail",
                    kwargs={"token": token, "photo_id": item.photo_id},
                ),
                "print_label": item.print_option.label,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "subtotal": item.subtotal,
            }
        )

    context = {
        "gallery": gallery,
        "order": order,
        "items": rows,
        "items_count": order.items_count,
        "total_price": order.total_price,
    }
    return render(request, "orders/order_confirmation.html", context)


@require_POST
def orders_cart_new_view(request, token):
    gallery = _get_accessible_gallery_or_404(token)
    session_key = _ensure_session_key(request)
    existing = get_draft_order(gallery=gallery, session_key=session_key)
    if existing:
        messages.info(request, "Rozpracovaný košík už existuje.")
        return redirect("orders-cart-detail", token=token)

    create_draft_order(gallery=gallery, session_key=session_key)
    messages.success(request, "Byl vytvořen nový košík.")
    return redirect("client-gallery", token=token)
