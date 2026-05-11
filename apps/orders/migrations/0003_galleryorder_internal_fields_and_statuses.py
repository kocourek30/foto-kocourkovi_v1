from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("orders", "0002_galleryorder_unique_draft_per_gallery_session"),
    ]

    operations = [
        migrations.AddField(
            model_name="galleryorder",
            name="internal_note",
            field=models.TextField(blank=True, verbose_name="Interní poznámka"),
        ),
        migrations.AddField(
            model_name="galleryorder",
            name="processed_at",
            field=models.DateTimeField(blank=True, null=True, verbose_name="Zpracováno"),
        ),
        migrations.AlterField(
            model_name="galleryorder",
            name="status",
            field=models.CharField(
                choices=[
                    ("draft", "Rozpracovaná"),
                    ("submitted", "Odeslaná"),
                    ("processing", "V řešení"),
                    ("completed", "Dokončená"),
                    ("cancelled", "Zrušená"),
                ],
                default="draft",
                max_length=16,
                verbose_name="Stav",
            ),
        ),
    ]

