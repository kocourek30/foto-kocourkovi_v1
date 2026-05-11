# Generated manually for milestone 2.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("accounts", "0001_initial"),
        ("clients", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Job",
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
                ("title", models.CharField(max_length=255, verbose_name="Název zakázky")),
                ("shooting_date", models.DateField(blank=True, null=True, verbose_name="Datum focení")),
                ("location", models.CharField(blank=True, max_length=255, verbose_name="Místo")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("draft", "Návrh"),
                            ("scheduled", "Naplánováno"),
                            ("shot", "Odfoceno"),
                            ("gallery_ready", "Galerie připravena"),
                            ("selection_in_progress", "Výběr probíhá"),
                            ("selection_confirmed", "Výběr potvrzen"),
                            ("closed", "Uzavřeno"),
                        ],
                        default="draft",
                        max_length=32,
                        verbose_name="Stav",
                    ),
                ),
                ("notes", models.TextField(blank=True, verbose_name="Poznámky")),
                (
                    "client",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="jobs",
                        to="clients.client",
                        verbose_name="Klient",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="created_jobs",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Vytvořil",
                    ),
                ),
            ],
            options={
                "verbose_name": "Zakázka",
                "verbose_name_plural": "Zakázky",
                "ordering": ["-shooting_date", "-created_at"],
            },
        ),
    ]

