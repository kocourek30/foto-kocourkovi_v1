from pathlib import Path
import os


BASE_DIR = Path(__file__).resolve().parent.parent.parent


def env(name: str, default: str | None = None) -> str | None:
    return os.getenv(name, default)


def env_list(name: str, default: list[str] | None = None) -> list[str]:
    raw = os.getenv(name, "")
    if raw.strip():
        return [item.strip() for item in raw.split(",") if item.strip()]
    return default or []


def env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


SECRET_KEY = env("DJANGO_SECRET_KEY", env("SECRET_KEY", "django-insecure-change-me"))
DEBUG = env_bool("DEBUG", False)
ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", [])
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS", [])
USE_X_FORWARDED_HOST = env_bool("USE_X_FORWARDED_HOST", True)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

INSTALLED_APPS = [
    "jazzmin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "apps.common.apps.CommonConfig",
    "apps.accounts.apps.AccountsConfig",
    "apps.clients.apps.ClientsConfig",
    "apps.jobs.apps.JobsConfig",
    "apps.galleries.apps.GalleriesConfig",
    "apps.photos.apps.PhotosConfig",
    "apps.orders.apps.OrdersConfig",
]

JAZZMIN_SETTINGS = {
    "site_title": "Foto Kocourkovi Admin",
    "site_header": "Foto Kocourkovi",
    "site_brand": "Foto Kocourkovi",
    "welcome_sign": "Vítejte v administraci",
    "copyright": "Foto Kocourkovi",
    "show_sidebar": True,
    "navigation_expanded": True,
    "hide_apps": [],
    "icons": {
        "accounts.User": "fas fa-user-shield",
        "clients.Client": "fas fa-user",
        "jobs.Job": "fas fa-briefcase",
        "galleries.Gallery": "fas fa-images",
        "photos.Photo": "fas fa-camera",
        "photos.PhotoVariant": "fas fa-image",
        "orders.GalleryPrintOption": "fas fa-tags",
        "orders.GalleryOrder": "fas fa-receipt",
        "orders.GalleryOrderItem": "fas fa-list",
    },
    "custom_css": "admin/custom.css",
}

JAZZMIN_UI_TWEAKS = {
    "theme": "default",
    "dark_mode_theme": None,
    "navbar": "navbar-white navbar-light",
    "sidebar": "sidebar-dark-primary",
    "brand_colour": "navbar-primary",
    "accent": "accent-indigo",
    "navbar_small_text": False,
    "sidebar_small_text": False,
    "footer_small_text": True,
    "body_small_text": False,
    "actions_sticky_top": True,
}

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB", "foto_kocourkovi"),
        "USER": env("POSTGRES_USER", "foto_kocourkovi"),
        "PASSWORD": env("POSTGRES_PASSWORD", "foto_kocourkovi"),
        "HOST": env("POSTGRES_HOST", "db"),
        "PORT": env("POSTGRES_PORT", "5432"),
    }
}

AUTH_USER_MODEL = "accounts.User"

LANGUAGE_CODE = "cs"
TIME_ZONE = "Europe/Prague"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

PHOTO_WATERMARK_TEXT = env("PHOTO_WATERMARK_TEXT", "Foto Kocourkovi - NAHLED")
PHOTO_WATERMARK_OPACITY = int(env("PHOTO_WATERMARK_OPACITY", "145"))
PHOTO_PREVIEW_MAX_SIZE = int(env("PHOTO_PREVIEW_MAX_SIZE", "768"))
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", "no-reply@foto-kocourkovi.cz")
ORDER_NOTIFICATION_EMAIL = env("ORDER_NOTIFICATION_EMAIL", "")
SITE_BRAND_NAME = env("SITE_BRAND_NAME", "Foto Kocourkovi")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
