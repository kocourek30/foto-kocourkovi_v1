from django.contrib import admin
from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import path, reverse

from apps.photos.forms import MultiPhotoUploadForm
from apps.photos.models import Photo, PhotoVariant
from apps.photos.services import PhotoVariantGenerationError, generate_photo_variants


class PhotoVariantInline(admin.TabularInline):
    model = PhotoVariant
    extra = 0


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ("id", "gallery", "caption", "sort_order", "is_active", "created_at")
    search_fields = ("caption", "gallery__title", "gallery__job__title")
    list_filter = ("is_active", "created_at", "updated_at")
    ordering = ("gallery", "sort_order", "id")
    autocomplete_fields = ("gallery",)
    readonly_fields = ("created_at", "updated_at")
    inlines = (PhotoVariantInline,)
    change_list_template = "admin/photos/photo/change_list.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "bulk-upload/",
                self.admin_site.admin_view(self.bulk_upload_view),
                name="photos_photo_bulk_upload",
            )
        ]
        return custom_urls + urls

    def bulk_upload_view(self, request):
        if request.method == "POST":
            form = MultiPhotoUploadForm(request.POST, request.FILES)
            files = request.FILES.getlist("files")
            if form.is_valid() and files:
                gallery = form.cleaned_data["gallery"]
                imported_count = 0
                failed = []
                start_order = (
                    Photo.objects.filter(gallery=gallery).order_by("-sort_order").values_list("sort_order", flat=True).first()
                    or 0
                )

                for index, uploaded_file in enumerate(files, start=1):
                    filename = uploaded_file.name
                    try:
                        photo = Photo.objects.create(
                            gallery=gallery,
                            original_file=uploaded_file,
                            original_filename=filename,
                            caption="",
                            sort_order=start_order + index,
                            is_active=True,
                        )
                        generate_photo_variants(photo)
                    except Exception as exc:
                        failed.append(f"{filename}: {exc}")
                    else:
                        imported_count += 1

                if imported_count:
                    self.message_user(
                        request,
                        f"Úspěšně importováno {imported_count} souborů.",
                        level=messages.SUCCESS,
                    )
                if failed:
                    self.message_user(
                        request,
                        f"Selhalo {len(failed)} souborů.",
                        level=messages.ERROR,
                    )
                    for fail_message in failed[:10]:
                        self.message_user(request, fail_message, level=messages.ERROR)
                    if len(failed) > 10:
                        self.message_user(
                            request,
                            f"A dalších {len(failed) - 10} chyb není vypsáno.",
                            level=messages.WARNING,
                        )

                changelist_url = reverse("admin:photos_photo_changelist")
                return redirect(f"{changelist_url}?gallery__id__exact={gallery.id}")

            if not files:
                self.message_user(
                    request,
                    "Nebyl vybrán žádný soubor.",
                    level=messages.ERROR,
                )
        else:
            form = MultiPhotoUploadForm()

        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "title": "Hromadný import fotek",
            "form": form,
        }
        return render(request, "admin/photos/photo/multi_upload.html", context)

    def save_model(self, request, obj, form, change):
        if obj.original_file and not obj.original_filename:
            obj.original_filename = obj.original_file.name.split("/")[-1]
        super().save_model(request, obj, form, change)
        try:
            generate_photo_variants(obj)
        except PhotoVariantGenerationError as exc:
            self.message_user(
                request,
                f"Fotka byla uložena, ale generování variant selhalo: {exc}",
                level=messages.ERROR,
            )
        else:
            self.message_user(
                request,
                "Varianty (thumbnail, preview, watermarked_preview) byly úspěšně vygenerovány.",
                level=messages.SUCCESS,
            )


@admin.register(PhotoVariant)
class PhotoVariantAdmin(admin.ModelAdmin):
    list_display = ("id", "photo", "variant_type", "width", "height", "created_at")
    search_fields = ("photo__caption", "photo__gallery__title")
    list_filter = ("variant_type", "created_at")
    ordering = ("photo", "variant_type", "id")
    autocomplete_fields = ("photo",)
    readonly_fields = ("created_at", "updated_at")
