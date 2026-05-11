import uuid
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum

from apps.common.models import TimeStampedModel


class GalleryPrintOption(TimeStampedModel):
    gallery = models.ForeignKey(
        "galleries.Gallery",
        on_delete=models.PROTECT,
        related_name="print_options",
        verbose_name="Galerie",
    )
    label = models.CharField("Formát", max_length=64)
    width_mm = models.PositiveIntegerField("Šířka (mm)", null=True, blank=True)
    height_mm = models.PositiveIntegerField("Výška (mm)", null=True, blank=True)
    price = models.DecimalField("Cena", max_digits=10, decimal_places=2)
    currency = models.CharField("Měna", max_length=3, default="CZK")
    is_active = models.BooleanField("Aktivní", default=True)
    sort_order = models.PositiveIntegerField("Pořadí", default=0)

    class Meta:
        verbose_name = "Tiskový formát galerie"
        verbose_name_plural = "Tiskové formáty galerie"
        ordering = ["gallery_id", "sort_order", "label", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["gallery", "label"],
                name="uniq_print_option_gallery_label",
            )
        ]

    def __str__(self) -> str:
        return f"{self.gallery.title} / {self.label}"


class OrderStatus(models.TextChoices):
    DRAFT = "draft", "Rozpracovaná"
    SUBMITTED = "submitted", "Odeslaná"
    PROCESSING = "processing", "V řešení"
    COMPLETED = "completed", "Dokončená"
    CANCELLED = "cancelled", "Zrušená"


class GalleryOrder(TimeStampedModel):
    gallery = models.ForeignKey(
        "galleries.Gallery",
        on_delete=models.PROTECT,
        related_name="orders",
        verbose_name="Galerie",
    )
    public_id = models.UUIDField("Veřejné ID", default=uuid.uuid4, unique=True, editable=False)
    session_key = models.CharField("Session key", max_length=64, null=True, blank=True)
    status = models.CharField(
        "Stav",
        max_length=16,
        choices=OrderStatus.choices,
        default=OrderStatus.DRAFT,
    )
    submitted_at = models.DateTimeField("Odesláno", null=True, blank=True)
    processed_at = models.DateTimeField("Zpracováno", null=True, blank=True)
    note = models.TextField("Poznámka", blank=True)
    internal_note = models.TextField("Interní poznámka", blank=True)
    customer_email = models.EmailField("E-mail klienta", blank=True)
    customer_first_name = models.CharField("Jméno klienta", max_length=120, blank=True)
    customer_last_name = models.CharField("Příjmení klienta", max_length=120, blank=True)

    class Meta:
        verbose_name = "Objednávka galerie"
        verbose_name_plural = "Objednávky galerie"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["gallery", "session_key"],
                condition=models.Q(status=OrderStatus.DRAFT),
                name="uniq_draft_order_gallery_session",
            )
        ]

    def __str__(self) -> str:
        return f"{self.public_id} ({self.get_status_display()})"

    @property
    def total_price(self) -> Decimal:
        total = (
            self.items.aggregate(
                total=Sum(models.F("quantity") * models.F("unit_price"), output_field=models.DecimalField(max_digits=12, decimal_places=2))
            )["total"]
            or Decimal("0.00")
        )
        return total

    @property
    def items_count(self) -> int:
        total = self.items.aggregate(total=Sum("quantity"))["total"] or 0
        return int(total)


class GalleryOrderItem(TimeStampedModel):
    order = models.ForeignKey(
        "orders.GalleryOrder",
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="Objednávka",
    )
    photo = models.ForeignKey(
        "photos.Photo",
        on_delete=models.PROTECT,
        related_name="order_items",
        verbose_name="Fotka",
    )
    print_option = models.ForeignKey(
        "orders.GalleryPrintOption",
        on_delete=models.PROTECT,
        related_name="order_items",
        verbose_name="Tiskový formát",
    )
    quantity = models.PositiveIntegerField("Počet", default=1)
    unit_price = models.DecimalField("Cena za kus", max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "Položka objednávky"
        verbose_name_plural = "Položky objednávky"
        ordering = ["order_id", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["order", "photo", "print_option"],
                name="uniq_order_photo_print_option",
            )
        ]

    def __str__(self) -> str:
        return f"{self.order.public_id} / {self.photo_id} / {self.print_option.label}"

    @property
    def subtotal(self) -> Decimal:
        return self.unit_price * self.quantity

    def clean(self):
        errors = {}
        if self.order_id and self.photo_id and self.photo.gallery_id != self.order.gallery_id:
            errors["photo"] = "Fotka musí patřit do stejné galerie jako objednávka."
        if self.order_id and self.print_option_id and self.print_option.gallery_id != self.order.gallery_id:
            errors["print_option"] = "Tiskový formát musí patřit do stejné galerie jako objednávka."
        if errors:
            raise ValidationError(errors)


class GalleryOrderEventType(models.TextChoices):
    DRAFT_CREATED = "draft_created", "Vytvořen draft"
    SUBMITTED = "submitted", "Odesláno klientem"
    STATUS_CHANGED = "status_changed", "Změna stavu"


class GalleryOrderEvent(TimeStampedModel):
    order = models.ForeignKey(
        "orders.GalleryOrder",
        on_delete=models.CASCADE,
        related_name="events",
        verbose_name="Objednávka",
    )
    event_type = models.CharField(
        "Typ události",
        max_length=32,
        choices=GalleryOrderEventType.choices,
    )
    from_status = models.CharField("Původní stav", max_length=16, blank=True)
    to_status = models.CharField("Nový stav", max_length=16, blank=True)
    message = models.TextField("Zpráva", blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_events",
        verbose_name="Vytvořil",
    )

    class Meta:
        verbose_name = "Událost objednávky"
        verbose_name_plural = "Události objednávky"
        ordering = ["-created_at", "-id"]

    def __str__(self) -> str:
        return f"{self.order.public_id} / {self.get_event_type_display()}"
