"""
Django settings for BetPlatform.
Environment-driven — never hardcode secrets.
Supports SQLite (dev) and PostgreSQL (production) via DATABASE_URL.
"""
import os
from pathlib import Path
import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, True),
    ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1", "bettingbros.vercel.app"]),
)
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY", default="django-insecure-CHANGE-ME")
DEBUG       = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "rest_framework",
    "corsheaders",
    "apps.accounts",
    "apps.sportsbook",
    "apps.odds",
    "apps.bets",
    "apps.wallet",
    "apps.casino",
    "apps.promotions",
    "apps.payments",
    "apps.notifications",
    "apps.content",
    "apps.adminpanel",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF    = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [BASE_DIR / "templates"],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.debug",
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
        "apps.bets.context_processors.bet_slip_count",
    ]},
}]

# ── Database: SQLite for dev, PostgreSQL for production ──────────────────────
# Set DATABASE_URL=postgres://user:pass@host:5432/dbname in production .env
DATABASES = {
    "default": env.db("DATABASE_URL", default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}")
}
# Ensure psycopg is used for postgres URLs
DATABASES["default"].setdefault("CONN_MAX_AGE", 60)

AUTH_USER_MODEL = "accounts.User"
LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = env("TIME_ZONE", default="UTC")
USE_I18N = True
USE_TZ   = True

STATIC_URL   = "/static/"
STATIC_ROOT  = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
MEDIA_URL    = "/media/"
MEDIA_ROOT   = BASE_DIR / "media"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework.authentication.SessionAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticatedOrReadOnly"],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
}

CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])
CORS_ALLOW_CREDENTIALS = True

EMAIL_BACKEND     = env("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")
EMAIL_HOST        = env("EMAIL_HOST", default="")
EMAIL_PORT        = env.int("EMAIL_PORT", default=587)
EMAIL_USE_TLS     = env.bool("EMAIL_USE_TLS", default=True)
EMAIL_HOST_USER   = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="noreply@betplatform.com")

# ── Cache ────────────────────────────────────────────────────────────────────
_REDIS_URL = env("REDIS_URL", default="")
if _REDIS_URL:
    CACHES = {"default": {"BACKEND": "django.core.cache.backends.redis.RedisCache", "LOCATION": _REDIS_URL}}
else:
    CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache", "LOCATION": "betplatform"}}

# ── Sessions ─────────────────────────────────────────────────────────────────
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_HTTPONLY    = False   # JS reads CSRF for fetch()
CSRF_COOKIE_SAMESITE    = "Lax"
SESSION_ENGINE          = "django.contrib.sessions.backends.db"

# ── Production security (auto-enabled when DEBUG=False) ──────────────────────
if not DEBUG:
    SECURE_HSTS_SECONDS           = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD           = True
    SECURE_SSL_REDIRECT           = True
    SESSION_COOKIE_SECURE         = True
    CSRF_COOKIE_SECURE            = True
    SECURE_BROWSER_XSS_FILTER     = True
    SECURE_CONTENT_TYPE_NOSNIFF   = True
    X_FRAME_OPTIONS               = "DENY"

# ── External APIs ─────────────────────────────────────────────────────────────
ODDS_API_KEY          = env("ODDS_API_KEY", default="")
ODDS_API_BASE_URL     = env("ODDS_API_BASE_URL", default="https://api.the-odds-api.com/v4")
SPORTS_DATA_API_KEY   = env("SPORTS_DATA_API_KEY", default="")

# ── Payment providers ─────────────────────────────────────────────────────────
# Stripe (international cards)
STRIPE_PUBLIC_KEY     = env("STRIPE_PUBLIC_KEY", default="")
STRIPE_SECRET_KEY     = env("STRIPE_SECRET_KEY", default="")
STRIPE_WEBHOOK_SECRET = env("STRIPE_WEBHOOK_SECRET", default="")

# PayPal (international)
PAYPAL_CLIENT_ID      = env("PAYPAL_CLIENT_ID", default="")
PAYPAL_CLIENT_SECRET  = env("PAYPAL_CLIENT_SECRET", default="")
PAYPAL_MODE           = env("PAYPAL_MODE", default="sandbox")  # sandbox | live

# Flutterwave (African local payments — MTN, Airtel, Zamtel, ZANACO, etc.)
FLUTTERWAVE_PUBLIC_KEY  = env("FLUTTERWAVE_PUBLIC_KEY", default="")
FLUTTERWAVE_SECRET_KEY  = env("FLUTTERWAVE_SECRET_KEY", default="")
FLUTTERWAVE_ENCRYPTION_KEY = env("FLUTTERWAVE_ENCRYPTION_KEY", default="")

# Paystack (West/East Africa — local cards, mobile money)
PAYSTACK_PUBLIC_KEY   = env("PAYSTACK_PUBLIC_KEY", default="")
PAYSTACK_SECRET_KEY   = env("PAYSTACK_SECRET_KEY", default="")

# MTN Mobile Money (direct integration)
MTN_MOMO_API_USER     = env("MTN_MOMO_API_USER", default="")
MTN_MOMO_API_KEY      = env("MTN_MOMO_API_KEY", default="")
MTN_MOMO_BASE_URL     = env("MTN_MOMO_BASE_URL", default="https://sandbox.momodeveloper.mtn.com")

# Airtel Money
AIRTEL_CLIENT_ID      = env("AIRTEL_CLIENT_ID", default="")
AIRTEL_CLIENT_SECRET  = env("AIRTEL_CLIENT_SECRET", default="")

# Zamtel Kwacha (Zambia)
ZAMTEL_API_KEY        = env("ZAMTEL_API_KEY", default="")

# ── Logging ───────────────────────────────────────────────────────────────────
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "{levelname} {asctime} {module} {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
    },
    "root": {"handlers": ["console"], "level": env("LOG_LEVEL", default="INFO")},
    "loggers": {
        "django": {"handlers": ["console"], "level": "WARNING", "propagate": False},
        "apps":   {"handlers": ["console"], "level": "DEBUG" if DEBUG else "INFO", "propagate": False},
    },
}
