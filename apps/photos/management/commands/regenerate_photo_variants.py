from django.core.management.base import BaseCommand, CommandError

from apps.photos.models import Photo
from apps.photos.services import PhotoVariantGenerationError, generate_photo_variants


class Command(BaseCommand):
    help = "Znovu vygeneruje thumbnail/preview/watermarked_preview varianty pro existující fotky."

    def add_arguments(self, parser):
        parser.add_argument("--gallery-id", type=int, help="Regenerovat jen fotky z vybrané galerie.")
        parser.add_argument("--photo-id", type=int, help="Regenerovat jen jednu konkrétní fotku.")
        parser.add_argument(
            "--only-missing",
            action="store_true",
            help="Regenerovat pouze fotky, kde chybí aspoň jedna varianta.",
        )

    def handle(self, *args, **options):
        photos = Photo.objects.select_related("gallery").all().order_by("id")

        if options["gallery_id"]:
            photos = photos.filter(gallery_id=options["gallery_id"])
        if options["photo_id"]:
            photos = photos.filter(id=options["photo_id"])

        if options["only_missing"]:
            photos = [photo for photo in photos if photo.variants.count() < 3]
        else:
            photos = list(photos)

        if not photos:
            self.stdout.write(self.style.WARNING("Nebyly nalezeny žádné fotky k regeneraci."))
            return

        total = len(photos)
        ok_count = 0
        fail_count = 0

        self.stdout.write(f"Regenerace variant pro {total} fotek...")
        for index, photo in enumerate(photos, start=1):
            try:
                generate_photo_variants(photo)
            except (PhotoVariantGenerationError, OSError) as exc:
                fail_count += 1
                self.stderr.write(
                    f"[{index}/{total}] Photo #{photo.id} ({photo.gallery.title}) - CHYBA: {exc}"
                )
            except Exception as exc:
                raise CommandError(f"Neočekávaná chyba při regeneraci Photo #{photo.id}: {exc}") from exc
            else:
                ok_count += 1
                self.stdout.write(f"[{index}/{total}] Photo #{photo.id} - OK")

        if fail_count:
            self.stdout.write(
                self.style.WARNING(
                    f"Regenerace dokončena: úspěch {ok_count}, selhání {fail_count}."
                )
            )
        else:
            self.stdout.write(self.style.SUCCESS(f"Regenerace dokončena: úspěch {ok_count}, selhání 0."))

