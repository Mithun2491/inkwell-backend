from pathlib import Path
from datetime import timedelta
import os
from decouple import config
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent


def cast_debug(value):
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() not in {
        "0", "false", "no", "off",
        "release", "prod", "production"
    }


def local_env_value(key):
    env_file = BASE_DIR / ".env"

    if not env_file.exists():
        return None

    for line in env_file.read_text().splitlines():
        line = line.strip()

        if (
            not line
            or line.startswith("#")
            or "=" not in line
        ):
            continue

        name, value = line.split("=", 1)

        if name.strip() == key:
            return value.strip().strip("\"'")

    return None


# ─────────────────────────────────────────────────────────────
# Core Settings
# ─────────────────────────────────────────────────────────────

SECRET_KEY = config(
    "SECRET_KEY",
    default="change-me-in-production"
)

DEBUG = cast_debug(
    local_env_value("DEBUG")
    or config("DEBUG", default=True)
)

ALLOWED_HOSTS = config(
    "ALLOWED_HOSTS",
    default=".onrender.com,localhost,127.0.0.1"
).split(",")


# ─────────────────────────────────────────────────────────────
# Apps
# ─────────────────────────────────────────────────────────────

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "cloudinary_storage",
    "cloudinary",
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_filters",
    "taggit",
    "drf_spectacular",
]

LOCAL_APPS = [
    "apps.users",
    "apps.posts",
    "apps.notifications",
]

INSTALLED_APPS = (
    DJANGO_APPS
    + THIRD_PARTY_APPS
    + LOCAL_APPS
)


# ─────────────────────────────────────────────────────────────
# Middleware
# ─────────────────────────────────────────────────────────────

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",

    # WhiteNoise
    "whitenoise.middleware.WhiteNoiseMiddleware",

    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# ─────────────────────────────────────────────────────────────
# URLs / WSGI
# ─────────────────────────────────────────────────────────────

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

AUTH_USER_MODEL = "users.User"


# ─────────────────────────────────────────────────────────────
# Templates
# ─────────────────────────────────────────────────────────────

TEMPLATES = [
    {
        "BACKEND":
            "django.template.backends.django."
            "DjangoTemplates",

        "DIRS": [],

        "APP_DIRS": True,

        "OPTIONS": {
            "context_processors": [
                "django.template."
                "context_processors.debug",

                "django.template."
                "context_processors.request",

                "django.contrib.auth."
                "context_processors.auth",

                "django.contrib.messages."
                "context_processors.messages",
            ],
        },
    },
]


# ─────────────────────────────────────────────────────────────
# Database (Render PostgreSQL + Local SQLite)
# ─────────────────────────────────────────────────────────────

DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
        conn_health_checks=True,
    )
}


# ─────────────────────────────────────────────────────────────
# Redis Cache (Upstash)
# ─────────────────────────────────────────────────────────────

CACHES = {
    "default": {
        "BACKEND":
            "django_redis.cache.RedisCache",

        "LOCATION": config(
            "REDIS_URL",
            default="redis://localhost:6379/1"
        ),

        "OPTIONS": {
            "CLIENT_CLASS":
                "django_redis.client."
                "DefaultClient",

            "CONNECTION_POOL_KWARGS": {
                "ssl_cert_reqs": None
            }
        },
    }
}


# ─────────────────────────────────────────────────────────────
# Celery
# ─────────────────────────────────────────────────────────────

CELERY_BROKER_URL = config(
    "REDIS_URL",
    default="redis://localhost:6379/0"
)

CELERY_RESULT_BACKEND = config(
    "REDIS_URL",
    default="redis://localhost:6379/0"
)

CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"


# ─────────────────────────────────────────────────────────────
# Static & Media
# ─────────────────────────────────────────────────────────────

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"


DEFAULT_AUTO_FIELD = (
    "django.db.models.BigAutoField"
)


# ─────────────────────────────────────────────────────────────
# DRF
# ─────────────────────────────────────────────────────────────

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt."
        "authentication.JWTAuthentication",
    ),

    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions."
        "IsAuthenticatedOrReadOnly",
    ),

    "DEFAULT_PAGINATION_CLASS":
        "apps.posts.pagination."
        "StandardPagination",

    "PAGE_SIZE": 10,

    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework."
        "DjangoFilterBackend",

        "rest_framework.filters."
        "SearchFilter",

        "rest_framework.filters."
        "OrderingFilter",
    ],

    "DEFAULT_SCHEMA_CLASS":
        "drf_spectacular.openapi."
        "AutoSchema",
}


# ─────────────────────────────────────────────────────────────
# JWT
# ─────────────────────────────────────────────────────────────

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME":
        timedelta(minutes=60),

    "REFRESH_TOKEN_LIFETIME":
        timedelta(days=7),

    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,

    "AUTH_HEADER_TYPES": (
        "Bearer",
    ),
}


# ─────────────────────────────────────────────────────────────
# CORS
# ─────────────────────────────────────────────────────────────

CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS",
    default=(
        "http://localhost:3000,"
        "http://localhost:5173"
    ),
).split(",")


# ─────────────────────────────────────────────────────────────
# API Docs
# ─────────────────────────────────────────────────────────────

SPECTACULAR_SETTINGS = {
    "TITLE": "MediumBlog API",
    "DESCRIPTION":
        "A developer blog platform like Medium",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

import cloudinary

CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.environ.get('CLOUDINARY_CLOUD_NAME'),
    'API_KEY': os.environ.get('CLOUDINARY_API_KEY'),
    'API_SECRET': os.environ.get('CLOUDINARY_API_SECRET'),
}

STORAGES = {
    "default": {
        "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}
