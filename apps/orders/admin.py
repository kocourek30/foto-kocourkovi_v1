import csv
from pathlib import Path

from django.contrib import admin, messages
from django.http import HttpResponse

from apps.orders.models import (
    GalleryOrder,
    GalleryOrderEvent,
    GalleryOrderItem,
    GalleryPrintOption,
    OrderStatus,
)
from apps.orders.services import transition_order_status


@admin.register(GalleryPrintOption)
class GalleryPrintOptionAdmin(admin.ModelAdmin):
    list_display = ("gallery", "label", "price", "currency", "is_active", "sort_order")
    list_filter = ("is_active", "currency", "created_at")
    search_fields = ("label", "gallery__title", "gallery__job__title")
    ordering = ("gallery", "sort_order", "label")
    autocomplete_fields = ("gallery",)


class GalleryOrderItemInline(admin.TabularInline):
    model = GalleryOrderItem
    extra = 0
    autocomplete_fields = ("photo", "print_option")
    readonly_fields = ("unit_price", "created_at", "updated_at")


class GalleryOrderEventInline(admin.TabularInline):
    model = GalleryOrderEvent
    extra = 0
    can_delete = False
    fields = ("created_at", "event_summary", "from_status", "to_status", "message", "created_by")
    readonly_fields = ("created_at", "event_summary", "from_status", "to_status", "message", "created_by")
    ordering = ("-created_at", "-id")

    def has_add_permission(self, request, obj=None):
        return False

    @admin.display(description="Událost")
    def event_summary(self, obj):
        return obj.get_event_type_display()


@admin.register(GalleryOrder)
class GalleryOrderAdmin(admin.ModelAdmin):
    list_display = ("public_id", "gallery", "status", "submitted_at", "items_count", "total_price", "created_at")
    list_filter = ("status", "created_at", "submitted_at", "processed_at")
    search_fields = ("public_id", "gallery__title", "gallery__job__title", "session_key")
    ordering = ("-created_at",)
    autocomplete_fields = ("gallery",)
    readonly_fields = ("public_id", "last_event_summary", "created_at", "updated_at", "submitted_at", "processed_at")
    inlines = (GalleryOrderItemInline, GalleryOrderEventInline)
    actions = (
        "mark_as_processing",
        "mark_as_completed",
        "mark_as_cancelled",
        "export_selected_orders_to_csv",
    )
    fieldsets = (
        (
            "Základ",
            {
                "fields": (
                    "public_id",
                    "gallery",
                    "status",
                    "last_event_summary",
                    "session_key",
                    "note",
                    "internal_note",
                )
            },
        ),
        (
            "Systém",
            {
                "fields": (
                    "submitted_at",
                    "processed_at",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    @admin.display(description="Poslední událost")
    def last_event_summary(self, obj):
        event = obj.events.select_related("created_by").order_by("-created_at", "-id").first()
        if not event:
            return "—"

        created_by = event.created_by.get_username() if event.created_by else "systém"
        to_status = self._status_label(event.to_status) if event.to_status else "beze změny stavu"
        return f"{event.created_at:%d.%m.%Y %H:%M} – {event.get_event_type_display()} – {to_status} – {created_by}"

    @staticmethod
    def _status_label(status_value: str) -> str:
        if not status_value:
            return ""
        for value, label in OrderStatus.choices:
            if value == status_value:
                return label
        return status_value

    @admin.action(description="Označit jako V řešení")
    def mark_as_processing(self, request, queryset):
        affected = 0
        for order in queryset.exclude(status__in=[OrderStatus.CANCELLED, OrderStatus.COMPLETED]):
            transition_order_status(
                order=order,
                to_status=OrderStatus.PROCESSING,
                created_by=request.user,
                message="Stav změněn z administrace.",
            )
            affected += 1
        self.message_user(request, f"Objednávek označených jako V řešení: {affected}", level=messages.SUCCESS)

    @admin.action(description="Označit jako Dokončené")
    def mark_as_completed(self, request, queryset):
        affected = 0
        for order in queryset.exclude(status=OrderStatus.CANCELLED):
            transition_order_status(
                order=order,
                to_status=OrderStatus.COMPLETED,
                created_by=request.user,
                message="Stav změněn z administrace.",
            )
            affected += 1
        self.message_user(request, f"Objednávek označených jako Dokončené: {affected}", level=messages.SUCCESS)

    @admin.action(description="Označit jako Zrušené")
    def mark_as_cancelled(self, request, queryset):
        affected = 0
        for order in queryset.exclude(status=OrderStatus.COMPLETED):
            transition_order_status(
                order=order,
                to_status=OrderStatus.CANCELLED,
                created_by=request.user,
                message="Stav změněn z administrace.",
            )
            affected += 1
        self.message_user(request, f"Objednávek označených jako Zrušené: {affected}", level=messages.SUCCESS)

    @admin.action(description="Export vybraných objednávek do CSV")
    def export_selected_orders_to_csv(self, request, queryset):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="orders_export.csv"'

        writer = csv.writer(response)
        writer.writerow(
            [
                "order_public_id",
                "gallery_title",
                "photo_id",
                "photo_original_filename",
                "photo_caption",
                "print_option_label",
                "quantity",
                "unit_price",
                "subtotal",
                "status",
                "customer_email",
                "customer_first_name",
                "customer_last_name",
            ]
        )
        for order in queryset.select_related("gallery").prefetch_related("items__photo", "items__print_option").order_by("created_at"):
            for item in order.items.all().order_by("id"):
                original_name = item.photo.original_filename or Path(item.photo.original_file.name).name
                writer.writerow(
                    [
                        str(order.public_id),
                        order.gallery.title,
                        item.photo_id,
                        original_name,
                        item.photo.caption,
                        item.print_option.label,
                        item.quantity,
                        item.unit_price,
                        item.subtotal,
                        order.status,
                        order.customer_email,
                        order.customer_first_name,
                        order.customer_last_name,
                    ]
                )
        return response
