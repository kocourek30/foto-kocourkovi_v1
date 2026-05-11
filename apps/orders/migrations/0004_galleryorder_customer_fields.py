from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("orders", "0003_galleryorder_internal_fields_and_statuses"),
    ]

    operations = [
        migrations.AddField(
            model_name="galleryorder",
            name="customer_email",
            field=models.EmailField(blank=True, max_length=254, verbose_name="E-mail klienta"),
        ),
        migrations.AddField(
            model_name="galleryorder",
            name="customer_first_name",
            field=models.CharField(blank=True, max_length=120, verbose_name="Jméno klienta"),
        ),
        migrations.AddField(
            model_name="galleryorder",
            name="customer_last_name",
            field=models.CharField(blank=True, max_length=120, verbose_name="Příjmení klienta"),
        ),
    ]

