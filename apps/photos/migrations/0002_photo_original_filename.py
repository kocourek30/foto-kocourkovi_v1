from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("photos", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="photo",
            name="original_filename",
            field=models.CharField(blank=True, max_length=255, verbose_name="Originální název souboru"),
        ),
    ]

