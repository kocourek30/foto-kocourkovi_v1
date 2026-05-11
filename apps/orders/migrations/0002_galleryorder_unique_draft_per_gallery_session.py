from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("orders", "0001_initial"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="galleryorder",
            constraint=models.UniqueConstraint(
                condition=models.Q(status="draft"),
                fields=("gallery", "session_key"),
                name="uniq_draft_order_gallery_session",
            ),
        ),
    ]
