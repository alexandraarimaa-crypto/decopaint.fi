"""Minimal isolated settings for the P0 security regression suite."""

from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "test-only-not-a-production-secret"
DEBUG = False
ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "users",
    "shop",
    "cart",
    "order",
    "pk_paytrail",
    "google_shopping",
    "blog",
    "mail",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

ROOT_URLCONF = "config.test_urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": False,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
            "loaders": [
                (
                    "django.template.loaders.locmem.Loader",
                    {
                        "order/cancelled.html": "Cancelled",
                        "order/pending.html": "Payment pending {{ order_id }}",
                        "profile/payment_details.html": "Payment {{ order.id }}",
                    },
                ),
                "django.template.loaders.app_directories.Loader",
            ],
        },
    }
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / ".test.sqlite3",
    }
}

AUTH_USER_MODEL = "users.CustomUser"
LOGIN_URL = "/user/login/"

# The production project uses a custom authentication backend that supports
# the legacy non-unique email field. These regression tests authenticate with
# force_login and do not exercise backend selection.
SILENCED_SYSTEM_CHECKS = ["auth.E003"]

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

LANGUAGE_CODE = "fi"
TIME_ZONE = "Europe/Helsinki"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
MEDIA_URL = "/media/"
CART_SESSION_ID = "cart"
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
DEFAULT_FROM_EMAIL = "tests@invalid.example"
DEFAULT_REPLY_TO_EMAIL = "info@decopaint.fi"
EMAIL_FROM_NAME = "Deco Paint Finland Oy"

PK_PAYTRAIL_API_URL = "https://services.paytrail.com/payments"
PK_PAYTRAIL_REDIRECT_SUCCESS_URL = "https://testserver/order/payment_success/"
PK_PAYTRAIL_REDIRECT_CANCEL_URL = "https://testserver/order/payment_cancel/"
PK_PAYTRAIL_MERCHANT_ID = "test-merchant"
PK_PAYTRAIL_MERCHANT_SECRET = "test-secret"
PK_PAYTRAIL_CURRENCY = "EUR"
PK_PAYTRAIL_LANGUAGE = "FI"

MERCHANT_SYNC_ENABLED = False
PAYMENT_DEBUG_LOGGING = False
ANALYTICS_ENABLED = False
GA4_MEASUREMENT_ID = "G-TESTONLY"
ANALYTICS_USER_ID_SALT = "test-only-analytics-salt"

Q_CLUSTER = {
    "name": "tests",
    "timeout": 60,
    "retry": 61,
    "sync": True,
}
