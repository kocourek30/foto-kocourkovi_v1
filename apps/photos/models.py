from django.db import models

from apps.common.models import TimeStampedModel


class VariantType(models.TextChoices):
    THUMBNAIL = "thumbnail", "Thumbnail"
    PREVIEW = "preview", "Náhled"
    WATERMARKED_PREVIEW = "watermarked_preview", "Náhled s vodoznakem"


class Photo(TimeStampedModel):
    gallery = models.ForeignKey(
        "galleries.Gallery",
        on_delete=models.PROTECT,
        related_name="photos",
        verbose_name="Galerie",
    )
    original_file = models.ImageField(
        "Originální soubor",
        upload_to="photos/originals/%Y/%m/",
    )
    original_filename = models.CharField("Originální název souboru", max_length=255, blank=True)
    caption = models.CharField("Titulek", max_length=255, blank=True)
    sort_order = models.PositiveIntegerField("Pořadí", default=0)
    is_active = models.BooleanField("Aktivní", default=True)

    class Meta:
        verbose_name = "Fotka"
        verbose_name_plural = "Fotky"
        ordering = ["sort_order", "id"]

    def __str__(self) -> str:
        return f"{self.gallery.title} / {self.id}"


class PhotoVariant(TimeStampedModel):
    photo = models.ForeignKey(
        "photos.Photo",
        on_delete=models.CASCADE,
        related_name="variants",
        verbose_name="Fotka",
    )
    variant_type = models.CharField(
        "Typ varianty",
        max_length=32,
        choices=VariantType.choices,
    )
    file = models.ImageField(
        "Soubor varianty",
        upload_to="photos/variants/%Y/%m/",
    )
    width = models.PositiveIntegerField("Šířka", null=True, blank=True)
    height = models.PositiveIntegerField("Výška", null=True, blank=True)

    class Meta:
        verbose_name = "Varianta fotky"
        verbose_name_plural = "Varianty fotek"
        ordering = ["photo_id", "variant_type", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["photo", "variant_type"],
                name="uniq_variant_per_photo_type",
            )
        ]

    def __str__(self) -> str:
        return f"{self.photo_id} / {self.variant_type}"
