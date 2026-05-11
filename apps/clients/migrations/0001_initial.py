# Generated manually for milestone 2.

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Client",
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
                ("name", models.CharField(max_length=255, verbose_name="Jméno")),
                ("email", models.EmailField(blank=True, max_length=254, verbose_name="E-mail")),
                ("phone", models.CharField(blank=True, max_length=50, verbose_name="Telefon")),
                ("notes", models.TextField(blank=True, verbose_name="Poznámky")),
            ],
            options={
                "verbose_name": "Klient",
                "verbose_name_plural": "Klienti",
                "ordering": ["name", "-created_at"],
            },
        ),
    ]

