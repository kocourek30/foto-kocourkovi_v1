import mimetypes

from django.core.files.storage import default_storage
from django.db.models import Prefetch, Sum
from django.http import FileResponse
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone

from apps.galleries.models import Gallery, GalleryStatus
from apps.orders.models import GalleryPrintOption
from apps.orders.services import get_cart_summary, get_draft_order, get_last_submitted_order
from apps.photos.models import Photo, PhotoVariant, VariantType


def _get_accessible_gallery_or_404(token: str) -> Gallery:
    gallery = get_object_or_404(Gallery, token=token)
    if gallery.status != GalleryStatus.PUBLISHED:
        raise Http404("Galerie není dostupná.")
    if gallery.expires_at is not None and timezone.now() > gallery.expires_at:
        raise Http404("Galerie není dostupná.")
    return gallery


def client_gallery_view(request, token):
    gallery = _get_accessible_gallery_or_404(token)
    if not request.session.session_key:
        request.session.save()
    session_key = request.session.session_key
    draft_order = get_draft_order(gallery=gallery, session_key=session_key)
    submitted_order = get_last_submitted_order(gallery=gallery, session_key=session_key)
    summary_order = draft_order or submitted_order
    gallery_filter = request.GET.get("filter", "all")
    if gallery_filter not in {"all", "selected"}:
        gallery_filter = "all"
    recently_added_photo_id = None
    added_photo_id_raw = request.GET.get("added_photo_id")
    if added_photo_id_raw:
        try:
            recently_added_photo_id = int(added_photo_id_raw)
        except (TypeError, ValueError):
            recently_added_photo_id = None
    cart_photo_quantities = {}
    if draft_order:
        cart_photo_quantities = {
            row["photo_id"]: row["total_quantity"]
            for row in draft_order.items.values("photo_id").annotate(total_quantity=Sum("quantity"))
        }
    selected_photos_count = len(cart_photo_quantities)
    selected_total_quantity = int(sum(cart_photo_quantities.values()))

    variants_qs = PhotoVariant.objects.filter(
        variant_type__in=[
            VariantType.THUMBNAIL,
            VariantType.PREVIEW,
            VariantType.WATERMARKED_PREVIEW,
        ]
    )

    photos_qs = (
        Photo.objects.filter(gallery=gallery, is_active=True)
        .order_by("sort_order", "id")
        .prefetch_related(Prefetch("variants", queryset=variants_qs))
    )

    all_photo_cards = []
    for photo in photos_qs:
        variant_map = {variant.variant_type: variant for variant in photo.variants.all()}

        thumb_variant = (
            variant_map.get(VariantType.THUMBNAIL)
            or variant_map.get(VariantType.WATERMARKED_PREVIEW)
            or variant_map.get(VariantType.PREVIEW)
        )
        preview_variant = (
            variant_map.get(VariantType.WATERMARKED_PREVIEW)
            or variant_map.get(VariantType.PREVIEW)
            or variant_map.get(VariantType.THUMBNAIL)
        )

        if not thumb_variant or not preview_variant:
            continue

        all_photo_cards.append(
            {
                "id": photo.id,
                "caption": photo.caption,
                "in_cart": photo.id in cart_photo_quantities,
                "cart_quantity": int(cart_photo_quantities.get(photo.id, 0) or 0),
                "just_added": photo.id == recently_added_photo_id,
                "thumb_url": reverse(
                    "client-gallery-photo-thumbnail",
                    kwargs={"token": gallery.token, "photo_id": photo.id},
                ),
                "preview_url": reverse(
                    "client-gallery-photo-preview",
                    kwargs={"token": gallery.token, "photo_id": photo.id},
                ),
                "width": preview_variant.width,
                "height": preview_variant.height,
            }
        )

    if gallery_filter == "selected":
        photos = [p for p in all_photo_cards if p["in_cart"]]
    else:
        photos = all_photo_cards

    context = {
        "gallery": gallery,
        "photos": photos,
        "photos_count": len(photos),
        "all_photos_count": len(all_photo_cards),
        "print_options": GalleryPrintOption.objects.filter(gallery=gallery, is_active=True).order_by("sort_order", "id"),
        "cart_photo_ids": list(cart_photo_quantities.keys()),
        "cart_photo_quantities": cart_photo_quantities,
        "selected_photos_count": selected_photos_count,
        "selected_total_quantity": selected_total_quantity,
        "gallery_filter": gallery_filter,
        "recently_added_photo_id": recently_added_photo_id,
        **(get_cart_summary(summary_order) if summary_order else {"items_count": 0, "total_price": 0}),
        "cart_locked": bool(submitted_order and not draft_order),
    }
    return render(request, "galleries/client_gallery.html", context)


def client_gallery_photo_thumbnail_view(request, token, photo_id):
    gallery = _get_accessible_gallery_or_404(token)
    photo = get_object_or_404(Photo, id=photo_id, gallery=gallery, is_active=True)

    variants = {
        variant.variant_type: variant
        for variant in photo.variants.filter(
            variant_type__in=[
                VariantType.THUMBNAIL,
                VariantType.WATERMARKED_PREVIEW,
                VariantType.PREVIEW,
            ]
        )
    }
    target = (
        variants.get(VariantType.THUMBNAIL)
        or variants.get(VariantType.WATERMARKED_PREVIEW)
        or variants.get(VariantType.PREVIEW)
    )
    if not target or not target.file:
        raise Http404("Náhled není dostupný.")

    file_handle = default_storage.open(target.file.name, "rb")
    content_type = mimetypes.guess_type(target.file.name)[0] or "application/octet-stream"
    response = FileResponse(file_handle, content_type=content_type)
    response["Cache-Control"] = "private, no-store"
    response["X-Content-Type-Options"] = "nosniff"
    return response


def client_gallery_photo_preview_view(request, token, photo_id):
    gallery = _get_accessible_gallery_or_404(token)
    photo = get_object_or_404(Photo, id=photo_id, gallery=gallery, is_active=True)

    variants = {
        variant.variant_type: variant
        for variant in photo.variants.filter(
            variant_type__in=[VariantType.WATERMARKED_PREVIEW, VariantType.PREVIEW]
        )
    }
    target = variants.get(VariantType.WATERMARKED_PREVIEW) or variants.get(VariantType.PREVIEW)
    if not target or not target.file:
        raise Http404("Náhled není dostupný.")

    file_handle = default_storage.open(target.file.name, "rb")
    content_type = mimetypes.guess_type(target.file.name)[0] or "application/octet-stream"
    response = FileResponse(file_handle, content_type=content_type)
    response["Cache-Control"] = "private, no-store"
    response["X-Content-Type-Options"] = "nosniff"
    return response
