# Generated manually for milestone 7.

import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("galleries", "0001_initial"),
        ("photos", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="GalleryOrder",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name="Veřejné ID")),
                ("session_key", models.CharField(blank=True, max_length=64, null=True, verbose_name="Session key")),
                (
                    "status",
                    models.CharField(
                        choices=[("draft", "Rozpracovaná"), ("submitted", "Odeslaná"), ("cancelled", "Zrušená")],
                        default="draft",
                        max_length=16,
                        verbose_name="Stav",
                    ),
                ),
                ("submitted_at", models.DateTimeField(blank=True, null=True, verbose_name="Odesláno")),
                ("note", models.TextField(blank=True, verbose_name="Poznámka")),
                (
                    "gallery",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="orders",
                        to="galleries.gallery",
                        verbose_name="Galerie",
                    ),
                ),
            ],
            options={
                "verbose_name": "Objednávka galerie",
                "verbose_name_plural": "Objednávky galerie",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="GalleryPrintOption",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("label", models.CharField(max_length=64, verbose_name="Formát")),
                ("width_mm", models.PositiveIntegerField(blank=True, null=True, verbose_name="Šířka (mm)")),
                ("height_mm", models.PositiveIntegerField(blank=True, null=True, verbose_name="Výška (mm)")),
                ("price", models.DecimalField(decimal_places=2, max_digits=10, verbose_name="Cena")),
                ("currency", models.CharField(default="CZK", max_length=3, verbose_name="Měna")),
                ("is_active", models.BooleanField(default=True, verbose_name="Aktivní")),
                ("sort_order", models.PositiveIntegerField(default=0, verbose_name="Pořadí")),
                (
                    "gallery",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="print_options",
                        to="galleries.gallery",
                        verbose_name="Galerie",
                    ),
                ),
            ],
            options={
                "verbose_name": "Tiskový formát galerie",
                "verbose_name_plural": "Tiskové formáty galerie",
                "ordering": ["gallery_id", "sort_order", "label", "id"],
            },
        ),
        migrations.CreateModel(
            name="GalleryOrderItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("quantity", models.PositiveIntegerField(default=1, verbose_name="Počet")),
                ("unit_price", models.DecimalField(decimal_places=2, max_digits=10, verbose_name="Cena za kus")),
                (
                    "order",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="items",
                        to="orders.galleryorder",
                        verbose_name="Objednávka",
                    ),
                ),
                (
                    "photo",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="order_items",
                        to="photos.photo",
                        verbose_name="Fotka",
                    ),
                ),
                (
                    "print_option",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="order_items",
                        to="orders.galleryprintoption",
                        verbose_name="Tiskový formát",
                    ),
                ),
            ],
            options={
                "verbose_name": "Položka objednávky",
                "verbose_name_plural": "Položky objednávky",
                "ordering": ["order_id", "id"],
            },
        ),
        migrations.AddConstraint(
            model_name="galleryprintoption",
            constraint=models.UniqueConstraint(fields=("gallery", "label"), name="uniq_print_option_gallery_label"),
        ),
        migrations.AddConstraint(
            model_name="galleryorderitem",
            constraint=models.UniqueConstraint(fields=("order", "photo", "print_option"), name="uniq_order_photo_print_option"),
        ),
    ]

