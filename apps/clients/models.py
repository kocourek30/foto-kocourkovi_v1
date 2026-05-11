from django.db import models

from apps.common.models import TimeStampedModel


class Client(TimeStampedModel):
    name = models.CharField("Jméno", max_length=255)
    email = models.EmailField("E-mail", blank=True)
    phone = models.CharField("Telefon", max_length=50, blank=True)
    notes = models.TextField("Poznámky", blank=True)

    class Meta:
        verbose_name = "Klient"
        verbose_name_plural = "Klienti"
        ordering = ["name", "-created_at"]

    def __str__(self) -> str:
        return self.name

