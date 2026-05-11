# Generated manually for milestone 3.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("jobs", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Gallery",
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
                ("title", models.CharField(max_length=255, verbose_name="Název galerie")),
                ("description", models.TextField(blank=True, verbose_name="Popis")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("draft", "Návrh"),
                            ("published", "Zveřejněná"),
                            ("archived", "Archivovaná"),
                        ],
                        default="draft",
                        max_length=16,
                        verbose_name="Stav",
                    ),
                ),
                ("selection_limit", models.PositiveIntegerField(blank=True, null=True, verbose_name="Limit výběru")),
                (
                    "token",
                    models.CharField(
                        db_index=True,
                        editable=False,
                        max_length=64,
                        unique=True,
                        verbose_name="Přístupový token",
                    ),
                ),
                ("expires_at", models.DateTimeField(blank=True, null=True, verbose_name="Platnost do")),
                (
                    "access_password_hint",
                    models.CharField(
                        blank=True,
                        default=None,
                        max_length=255,
                        null=True,
                        verbose_name="Heslo/PIN (rezerva)",
                    ),
                ),
                (
                    "job",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="galleries",
                        to="jobs.job",
                        verbose_name="Zakázka",
                    ),
                ),
            ],
            options={
                "verbose_name": "Galerie",
                "verbose_name_plural": "Galerie",
                "ordering": ["-created_at"],
            },
        ),
    ]

