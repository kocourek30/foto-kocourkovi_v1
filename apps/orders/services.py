from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.galleries.models import Gallery
from apps.orders.emails import send_order_submitted_notifications
from apps.orders.models import (
    GalleryOrder,
    GalleryOrderEvent,
    GalleryOrderEventType,
    GalleryOrderItem,
    GalleryPrintOption,
    OrderStatus,
)
from apps.photos.models import Photo


def get_draft_order(gallery: Gallery, session_key: str) -> GalleryOrder | None:
    return (
        GalleryOrder.objects.filter(
            gallery=gallery,
            session_key=session_key,
            status=OrderStatus.DRAFT,
        )
        .order_by("-created_at")
        .first()
    )


def create_draft_order(gallery: Gallery, session_key: str) -> GalleryOrder:
    existing = get_draft_order(gallery=gallery, session_key=session_key)
    if existing:
        return existing

    try:
        with transaction.atomic():
            order = GalleryOrder.objects.create(
                gallery=gallery,
                session_key=session_key,
                status=OrderStatus.DRAFT,
            )
            create_order_event(
                order=order,
                event_type=GalleryOrderEventType.DRAFT_CREATED,
                to_status=OrderStatus.DRAFT,
                message="Klient vytvořil nový košík.",
            )
            return order
    except IntegrityError:
        fallback = get_draft_order(gallery=gallery, session_key=session_key)
        if fallback is None:
            raise RuntimeError("Nepodařilo se načíst ani vytvořit rozpracovanou objednávku.")
        return fallback


def get_or_create_draft_order(gallery: Gallery, session_key: str) -> GalleryOrder:
    return get_draft_order(gallery=gallery, session_key=session_key) or create_draft_order(
        gallery=gallery,
        session_key=session_key,
    )


def get_last_submitted_order(gallery: Gallery, session_key: str) -> GalleryOrder | None:
    return (
        GalleryOrder.objects.filter(
            gallery=gallery,
            session_key=session_key,
            status=OrderStatus.SUBMITTED,
        )
        .order_by("-submitted_at", "-created_at")
        .first()
    )


def add_item_to_cart(
    order: GalleryOrder,
    photo: Photo,
    print_option: GalleryPrintOption,
    quantity: int,
) -> GalleryOrderItem:
    if quantity < 1:
        raise ValidationError("Množství musí být alespoň 1.")
    if order.gallery_id != photo.gallery_id:
        raise ValidationError("Fotka nepatří do stejné galerie jako objednávka.")
    if order.gallery_id != print_option.gallery_id:
        raise ValidationError("Tiskový formát nepatří do stejné galerie jako objednávka.")
    if not print_option.is_active:
        raise ValidationError("Tiskový formát není aktivní.")

    item, created = GalleryOrderItem.objects.get_or_create(
        order=order,
        photo=photo,
        print_option=print_option,
        defaults={"quantity": quantity, "unit_price": print_option.price},
    )
    if not created:
        item.quantity += quantity
        item.save(update_fields=["quantity", "updated_at"])
    return item


def remove_item_from_cart(order: GalleryOrder, item: GalleryOrderItem) -> None:
    if item.order_id != order.id:
        raise ValidationError("Položka nepatří do aktuálního košíku.")
    item.delete()


def update_item_quantity(order: GalleryOrder, item: GalleryOrderItem, quantity: int) -> GalleryOrderItem:
    if item.order_id != order.id:
        raise ValidationError("Položka nepatří do aktuálního košíku.")
    if quantity < 1:
        raise ValidationError("Množství musí být alespoň 1.")

    item.quantity = quantity
    item.save(update_fields=["quantity", "updated_at"])
    return item


def get_cart_summary(order: GalleryOrder) -> dict[str, int | Decimal]:
    return {
        "items_count": order.items_count,
        "total_price": order.total_price,
    }


def create_order_event(
    *,
    order: GalleryOrder,
    event_type: str,
    from_status: str = "",
    to_status: str = "",
    message: str = "",
    created_by=None,
) -> GalleryOrderEvent:
    return GalleryOrderEvent.objects.create(
        order=order,
        event_type=event_type,
        from_status=from_status,
        to_status=to_status,
        message=message,
        created_by=created_by,
    )


def transition_order_status(
    *,
    order: GalleryOrder,
    to_status: str,
    created_by=None,
    message: str = "",
) -> GalleryOrder:
    from_status = order.status
    if from_status == to_status:
        return order

    order.status = to_status
    if to_status == OrderStatus.COMPLETED:
        order.processed_at = timezone.now()
    elif to_status in {OrderStatus.PROCESSING, OrderStatus.CANCELLED}:
        order.processed_at = None

    order.save(update_fields=["status", "processed_at", "updated_at"])
    create_order_event(
        order=order,
        event_type=GalleryOrderEventType.STATUS_CHANGED,
        from_status=from_status,
        to_status=to_status,
        message=message,
        created_by=created_by,
    )
    return order


def submit_order(order: GalleryOrder) -> GalleryOrder:
    if order.status != OrderStatus.DRAFT:
        raise ValidationError("Objednávku lze odeslat pouze ze stavu rozpracovaná.")
    if not order.items.exists():
        raise ValidationError("Objednávka je prázdná.")

    with transaction.atomic():
        from_status = order.status
        order.status = OrderStatus.SUBMITTED
        order.submitted_at = timezone.now()
        order.processed_at = None
        order.save(update_fields=["status", "submitted_at", "processed_at", "updated_at"])
        create_order_event(
            order=order,
            event_type=GalleryOrderEventType.SUBMITTED,
            from_status=from_status,
            to_status=OrderStatus.SUBMITTED,
            message="Objednávka byla odeslána klientem.",
        )

    send_order_submitted_notifications(order)
    return order
