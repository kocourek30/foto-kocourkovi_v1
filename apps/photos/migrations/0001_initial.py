# Generated manually for milestone 4.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("galleries", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Photo",
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
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "original_file",
                    models.ImageField(upload_to="photos/originals/%Y/%m/", verbose_name="Originální soubor"),
                ),
                ("caption", models.CharField(blank=True, max_length=255, verbose_name="Titulek")),
                ("sort_order", models.PositiveIntegerField(default=0, verbose_name="Pořadí")),
                ("is_active", models.BooleanField(default=True, verbose_name="Aktivní")),
                (
                    "gallery",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="photos",
                        to="galleries.gallery",
                        verbose_name="Galerie",
                    ),
                ),
            ],
            options={
                "verbose_name": "Fotka",
                "verbose_name_plural": "Fotky",
                "ordering": ["sort_order", "id"],
            },
        ),
        migrations.CreateModel(
            name="PhotoVariant",
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
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "variant_type",
                    models.CharField(
                        choices=[
                            ("thumbnail", "Thumbnail"),
                            ("preview", "Náhled"),
                            ("watermarked_preview", "Náhled s vodoznakem"),
                        ],
                        max_length=32,
                        verbose_name="Typ varianty",
                    ),
                ),
                (
                    "file",
                    models.ImageField(upload_to="photos/variants/%Y/%m/", verbose_name="Soubor varianty"),
                ),
                ("width", models.PositiveIntegerField(blank=True, null=True, verbose_name="Šířka")),
                ("height", models.PositiveIntegerField(blank=True, null=True, verbose_name="Výška")),
                (
                    "photo",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="variants",
                        to="photos.photo",
                        verbose_name="Fotka",
                    ),
                ),
            ],
            options={
                "verbose_name": "Varianta fotky",
                "verbose_name_plural": "Varianty fotek",
                "ordering": ["photo_id", "variant_type", "id"],
            },
        ),
        migrations.AddConstraint(
            model_name="photovariant",
            constraint=models.UniqueConstraint(fields=("photo", "variant_type"), name="uniq_variant_per_photo_type"),
        ),
    ]

