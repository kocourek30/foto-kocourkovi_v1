from io import BytesIO
from pathlib import Path

from django.contrib import admin
from django.http import HttpResponse

from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from apps.galleries.models import Gallery
from apps.photos.models import Photo, VariantType


@admin.register(Gallery)
class GalleryAdmin(admin.ModelAdmin):
    list_display = ("title", "job", "status", "selection_limit", "expires_at", "created_at")
    search_fields = ("title", "job__title", "job__client__name", "token")
    list_filter = ("status", "created_at", "expires_at")
    ordering = ("-created_at",)
    autocomplete_fields = ("job",)
    readonly_fields = ("token", "created_at", "updated_at")
    actions = ("export_photo_index_pdf",)

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "job",
                    "title",
                    "description",
                    "status",
                    "selection_limit",
                    "expires_at",
                    "access_password_hint",
                    "token",
                )
            },
        ),
        ("Systémové údaje", {"fields": ("created_at", "updated_at")}),
    )

    @admin.action(description="Vygenerovat PDF index fotek")
    def export_photo_index_pdf(self, request, queryset):
        gallery = queryset.order_by("id").first()
        if not gallery:
            self.message_user(request, "Není vybraná žádná galerie.")
            return

        photos = (
            Photo.objects.filter(gallery=gallery, is_active=True)
            .prefetch_related("variants")
            .order_by("sort_order", "id")
        )

        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="gallery_{gallery.id}_photo_index.pdf"'

        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4)
        page_width, page_height = A4

        margin = 30
        header_y = page_height - margin
        cols = 3
        rows = 4
        slot_w = (page_width - 2 * margin) / cols
        slot_h = (page_height - 140) / rows
        image_h = slot_h - 40

        def draw_header():
            pdf.setFont("Helvetica-Bold", 14)
            pdf.drawString(margin, header_y, f"Index fotek: {gallery.title}")
            pdf.setFont("Helvetica", 9)
            pdf.drawString(margin, header_y - 15, "Instrukce: U každé fotky si poznamenejte ID a požadovaný formát tisku.")

        draw_header()
        index = 0

        for photo in photos:
            if index > 0 and index % (cols * rows) == 0:
                pdf.showPage()
                draw_header()

            position = index % (cols * rows)
            row = position // cols
            col = position % cols
            x = margin + col * slot_w
            y_top = page_height - 80 - row * slot_h
            y_bottom = y_top - image_h

            variants = {variant.variant_type: variant for variant in photo.variants.all()}
            img_variant = variants.get(VariantType.THUMBNAIL) or variants.get(VariantType.PREVIEW) or variants.get(VariantType.WATERMARKED_PREVIEW)

            if img_variant and img_variant.file:
                try:
                    with img_variant.file.open("rb") as fh:
                        image_reader = ImageReader(fh)
                        pdf.drawImage(
                            image_reader,
                            x,
                            y_bottom,
                            width=slot_w - 8,
                            height=image_h - 8,
                            preserveAspectRatio=True,
                            anchor="c",
                        )
                except Exception:
                    pdf.setFont("Helvetica", 9)
                    pdf.drawString(x + 4, y_bottom + 10, "Náhled nedostupný")
            else:
                pdf.setFont("Helvetica", 9)
                pdf.drawString(x + 4, y_bottom + 10, "Náhled nedostupný")

            original_name = photo.original_filename or Path(photo.original_file.name).name
            pdf.setFont("Helvetica-Bold", 9)
            pdf.drawString(x + 2, y_bottom - 12, f"ID: {photo.id}")
            pdf.setFont("Helvetica", 8)
            pdf.drawString(x + 2, y_bottom - 24, f"Soubor: {original_name[:38]}")
            if photo.caption:
                pdf.drawString(x + 2, y_bottom - 36, f"Titulek: {photo.caption[:34]}")

            index += 1

        pdf.save()
        response.write(buffer.getvalue())
        return response
