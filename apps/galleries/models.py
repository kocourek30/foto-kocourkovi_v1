import secrets

from django.db import models

from apps.common.models import TimeStampedModel


class GalleryStatus(models.TextChoices):
    DRAFT = "draft", "Návrh"
    PUBLISHED = "published", "Zveřejněná"
    ARCHIVED = "archived", "Archivovaná"


class Gallery(TimeStampedModel):
    job = models.ForeignKey(
        "jobs.Job",
        on_delete=models.PROTECT,
        related_name="galleries",
        verbose_name="Zakázka",
    )
    title = models.CharField("Název galerie", max_length=255)
    description = models.TextField("Popis", blank=True)
    status = models.CharField(
        "Stav",
        max_length=16,
        choices=GalleryStatus.choices,
        default=GalleryStatus.DRAFT,
    )
    selection_limit = models.PositiveIntegerField("Limit výběru", null=True, blank=True)
    token = models.CharField(
        "Přístupový token",
        max_length=64,
        unique=True,
        db_index=True,
        editable=False,
    )
    expires_at = models.DateTimeField("Platnost do", null=True, blank=True)
    access_password_hint = models.CharField(
        "Heslo/PIN (rezerva)",
        max_length=255,
        null=True,
        blank=True,
        default=None,
    )

    class Meta:
        verbose_name = "Galerie"
        verbose_name_plural = "Galerie"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.title} ({self.job.title})"

    @staticmethod
    def _generate_token() -> str:
        # 32 bytů dává dostatečně silný a neprůhledný token; URL-safe varianta
        # se vejde do 64 znaků a je vhodná do odkazu.
        return secrets.token_urlsafe(32)

    def save(self, *args, **kwargs):
        if not self.token:
            while True:
                candidate = self._generate_token()
                if not Gallery.objects.filter(token=candidate).exists():
                    self.token = candidate
                    break
        super().save(*args, **kwargs)

