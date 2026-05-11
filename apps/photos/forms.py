from django import forms

from apps.galleries.models import Gallery, GalleryStatus


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    widget = MultipleFileInput

    def clean(self, data, initial=None):
        single_clean = super().clean

        if not data:
            raise forms.ValidationError("Vyber alespoň jeden soubor.")

        if isinstance(data, (list, tuple)):
            cleaned = [single_clean(item, initial) for item in data if item]
        else:
            cleaned = [single_clean(data, initial)]

        if not cleaned:
            raise forms.ValidationError("Vyber alespoň jeden soubor.")
        return cleaned


class MultiPhotoUploadForm(forms.Form):
    gallery = forms.ModelChoiceField(
        label="Galerie",
        queryset=Gallery.objects.filter(status=GalleryStatus.PUBLISHED).order_by("-created_at"),
    )
    files = MultipleFileField(
        label="Soubory",
        widget=MultipleFileInput(attrs={"accept": "image/*"}),
        required=True,
    )
