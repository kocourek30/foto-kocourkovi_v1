from django.urls import path

from apps.galleries.views import (
    client_gallery_photo_preview_view,
    client_gallery_photo_thumbnail_view,
    client_gallery_view,
)

urlpatterns = [
    path("g/<str:token>/", client_gallery_view, name="client-gallery"),
    path(
        "g/<str:token>/p/<int:photo_id>/preview/",
        client_gallery_photo_preview_view,
        name="client-gallery-photo-preview",
    ),
    path(
        "g/<str:token>/p/<int:photo_id>/thumbnail/",
        client_gallery_photo_thumbnail_view,
        name="client-gallery-photo-thumbnail",
    ),
]
