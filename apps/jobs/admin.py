from django.contrib import admin

from apps.jobs.models import Job


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("title", "client", "shooting_date", "status", "created_by", "created_at")
    search_fields = ("title", "client__name", "client__email", "location")
    list_filter = ("status", "shooting_date", "created_at", "updated_at")
    ordering = ("-shooting_date", "-created_at")
    autocomplete_fields = ("client", "created_by")

