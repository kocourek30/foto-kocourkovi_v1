from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile
from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError

from apps.photos.models import Photo, PhotoVariant, VariantType


class PhotoVariantGenerationError(Exception):
    """Raised when generating photo variants fails."""


@dataclass(frozen=True)
class VariantSpec:
    variant_type: str
    max_side: int
    watermarked: bool = False


def _get_variant_specs() -> tuple[VariantSpec, ...]:
    preview_max_side = getattr(settings, "PHOTO_PREVIEW_MAX_SIZE", 768)
    try:
        preview_max_side = int(preview_max_side)
    except (TypeError, ValueError):
        preview_max_side = 768
    preview_max_side = max(500, min(1600, preview_max_side))
    return (
        VariantSpec(variant_type=VariantType.THUMBNAIL, max_side=400),
        VariantSpec(variant_type=VariantType.PREVIEW, max_side=preview_max_side),
        VariantSpec(variant_type=VariantType.WATERMARKED_PREVIEW, max_side=preview_max_side, watermarked=True),
    )

DEFAULT_WATERMARK_TEXT = "PREVIEW"
DEFAULT_WATERMARK_OPACITY = 145


def generate_photo_variants(photo: Photo, watermark_text: str | None = None) -> None:
    """Synchronously create or update variants for a stored photo."""
    if not photo.original_file:
        raise PhotoVariantGenerationError("Fotka nemá nahraný originální soubor.")

    try:
        photo.original_file.open("rb")
        with Image.open(photo.original_file) as source_image:
            prepared_source = _normalize_source_image(source_image)
            for spec in _get_variant_specs():
                variant_image = _resize_to_max_side(prepared_source, spec.max_side)
                if spec.watermarked:
                    variant_image = _apply_text_watermark(
                        variant_image,
                        _resolve_watermark_text(watermark_text),
                        _resolve_watermark_opacity(),
                    )
                file_name, file_content, width, height = _serialize_variant_image(photo, spec, variant_image)
                _upsert_variant(photo, spec.variant_type, file_name, file_content, width, height)
    except (UnidentifiedImageError, OSError) as exc:
        raise PhotoVariantGenerationError("Originální soubor není validní obrázek.") from exc
    finally:
        photo.original_file.close()


def _normalize_source_image(image: Image.Image) -> Image.Image:
    # Normalized color mode avoids edge-cases during resize/save for mixed source formats.
    if image.mode in {"RGBA", "LA", "P"}:
        return image.convert("RGBA")
    return image.convert("RGB")


def _resize_to_max_side(image: Image.Image, max_side: int) -> Image.Image:
    variant = image.copy()
    variant.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
    return variant


def _resolve_watermark_text(explicit_text: str | None) -> str:
    if explicit_text is not None and explicit_text.strip():
        return explicit_text.strip()
    return str(getattr(settings, "PHOTO_WATERMARK_TEXT", DEFAULT_WATERMARK_TEXT)).strip() or DEFAULT_WATERMARK_TEXT


def _resolve_watermark_opacity() -> int:
    value = getattr(settings, "PHOTO_WATERMARK_OPACITY", DEFAULT_WATERMARK_OPACITY)
    try:
        value = int(value)
    except (TypeError, ValueError):
        value = DEFAULT_WATERMARK_OPACITY
    return max(60, min(220, value))


def _apply_text_watermark(image: Image.Image, text: str, opacity: int) -> Image.Image:
    base = image.convert("RGBA")
    overlay = Image.new("RGBA", base.size, (255, 255, 255, 0))
    font = ImageFont.load_default()
    text = (text or DEFAULT_WATERMARK_TEXT).strip() or DEFAULT_WATERMARK_TEXT
    watermark_text = f"{text} • PROOF"

    pattern = Image.new("RGBA", (360, 120), (255, 255, 255, 0))
    draw = ImageDraw.Draw(pattern)
    # Draw twice with a tiny offset for stronger readability without external fonts.
    draw.text((10, 46), watermark_text, fill=(255, 255, 255, opacity), font=font)
    draw.text((11, 45), watermark_text, fill=(255, 255, 255, min(255, opacity + 20)), font=font)
    rotated = pattern.rotate(30, expand=True)

    step_x = max(130, rotated.width // 3)
    step_y = max(95, rotated.height // 3)
    for y in range(-rotated.height, base.height + rotated.height, step_y):
        for x in range(-rotated.width, base.width + rotated.width, step_x):
            overlay.alpha_composite(rotated, dest=(x, y))

    watermarked = Image.alpha_composite(base, overlay)
    return watermarked


def _serialize_variant_image(photo: Photo, spec: VariantSpec, image: Image.Image) -> tuple[str, ContentFile, int, int]:
    width, height = image.size
    stem = Path(photo.original_file.name).stem or f"photo-{photo.pk}"
    base_name = f"{stem}_{spec.variant_type}"

    if image.mode in {"RGBA", "LA"}:
        format_name = "PNG"
        extension = "png"
        output_image = image
        save_kwargs = {}
    else:
        format_name = "JPEG"
        extension = "jpg"
        output_image = image.convert("RGB")
        save_kwargs = {"quality": 85, "optimize": True}

    buffer = BytesIO()
    output_image.save(buffer, format=format_name, **save_kwargs)
    buffer.seek(0)
    return f"{base_name}.{extension}", ContentFile(buffer.read()), width, height


def _upsert_variant(
    photo: Photo,
    variant_type: str,
    file_name: str,
    file_content: ContentFile,
    width: int,
    height: int,
) -> None:
    variant, _ = PhotoVariant.objects.get_or_create(
        photo=photo,
        variant_type=variant_type,
    )
    variant.file.save(file_name, file_content, save=False)
    variant.width = width
    variant.height = height
    variant.save()
