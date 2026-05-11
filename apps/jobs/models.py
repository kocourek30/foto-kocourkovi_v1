from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel


class JobStatus(models.TextChoices):
    DRAFT = "draft", "Návrh"
    SCHEDULED = "scheduled", "Naplánováno"
    SHOT = "shot", "Odfoceno"
    GALLERY_READY = "gallery_ready", "Galerie připravena"
    SELECTION_IN_PROGRESS = "selection_in_progress", "Výběr probíhá"
    SELECTION_CONFIRMED = "selection_confirmed", "Výběr potvrzen"
    CLOSED = "closed", "Uzavřeno"


class Job(TimeStampedModel):
    client = models.ForeignKey(
        "clients.Client",
        on_delete=models.PROTECT,
        related_name="jobs",
        verbose_name="Klient",
    )
    title = models.CharField("Název zakázky", max_length=255)
    shooting_date = models.DateField("Datum focení", null=True, blank=True)
    location = models.CharField("Místo", max_length=255, blank=True)
    status = models.CharField(
        "Stav",
        max_length=32,
        choices=JobStatus.choices,
        default=JobStatus.DRAFT,
    )
    notes = models.TextField("Poznámky", blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_jobs",
        verbose_name="Vytvořil",
    )

    class Meta:
        verbose_name = "Zakázka"
        verbose_name_plural = "Zakázky"
        ordering = ["-shooting_date", "-created_at"]

    def __str__(self) -> str:
        return f"{self.title} ({self.client.name})"

