from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("orders", "0004_galleryorder_customer_fields"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="GalleryOrderEvent",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Vytvořeno")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Upraveno")),
                (
                    "event_type",
                    models.CharField(
                        choices=[
                            ("draft_created", "Vytvořen draft"),
                            ("submitted", "Odesláno klientem"),
                            ("status_changed", "Změna stavu"),
                        ],
                        max_length=32,
                        verbose_name="Typ události",
                    ),
                ),
                ("from_status", models.CharField(blank=True, max_length=16, verbose_name="Původní stav")),
                ("to_status", models.CharField(blank=True, max_length=16, verbose_name="Nový stav")),
                ("message", models.TextField(blank=True, verbose_name="Zpráva")),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="order_events",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Vytvořil",
                    ),
                ),
                (
                    "order",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="events",
                        to="orders.galleryorder",
                        verbose_name="Objednávka",
                    ),
                ),
            ],
            options={
                "verbose_name": "Událost objednávky",
                "verbose_name_plural": "Události objednávky",
                "ordering": ["-created_at", "-id"],
            },
        ),
    ]
