import os
import secrets
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured


BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name, default=""):
    return [item.strip() for item in os.environ.get(name, default).split(",") if item.strip()]


DEBUG = env_bool("DJANGO_DEBUG", False)
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = secrets.token_urlsafe(50)
    else:
        raise ImproperlyConfigured("DJANGO_SECRET_KEY is required when DJANGO_DEBUG is false.")

ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS")

INSTALLED_APPS = [
    "admin_interface",
    "colorfield",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "modeltranslation",
    "django_q",
    "solo",
    "tinymce",
    "users",
    "shop",
    "cart",
    "order",
    "pk_paytrail",
    "pk_postnord",
    "google_shopping",
    "mail",
    "services",
    "courses",
    "blog",
    "b2b",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "shop.language_middleware.CountryDefaultLanguageMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "cart.middleware.CartUserUpdateMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "cart.context_processors.cart",
                "shop.context_processors.store_settings",
            ],
        },
    }
]

if os.environ.get("DB_ENGINE", "sqlite").lower() == "mysql":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": os.environ.get("DB_NAME", ""),
            "USER": os.environ.get("DB_USER", ""),
            "PASSWORD": os.environ.get("DB_PASSWORD", ""),
            "HOST": os.environ.get("DB_HOST", "127.0.0.1"),
            "PORT": os.environ.get("DB_PORT", "3306"),
            "CONN_MAX_AGE": int(os.environ.get("DB_CONN_MAX_AGE", "60")),
            "OPTIONS": {"charset": "utf8mb4"},
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": Path(os.environ.get("SQLITE_PATH", BASE_DIR / "db.sqlite3")),
        }
    }

AUTH_USER_MODEL = "users.CustomUser"
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "fi"
LANGUAGES = [("fi", "Finnish"), ("sv", "Swedish"), ("en", "English")]
TIME_ZONE = "Europe/Helsinki"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = Path(os.environ.get("STATIC_ROOT", BASE_DIR / "staticfiles"))
MEDIA_URL = "/media/"
MEDIA_ROOT = Path(os.environ.get("MEDIA_ROOT", BASE_DIR / "media"))

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"
CART_SESSION_ID = "cart"
LOGIN_URL = "/user/login/"

EMAIL_BACKEND = os.environ.get(
    "EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend"
)
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "noreply@localhost")
DEFAULT_REPLY_TO_EMAIL = os.environ.get("DEFAULT_REPLY_TO_EMAIL", "info@decopaint.fi")
EMAIL_FROM_NAME = os.environ.get("EMAIL_FROM_NAME", "Deco Paint Finland Oy")
EMAIL_HOST = os.environ.get("EMAIL_HOST", "")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
DJANGO_Q_EMAIL_BACKEND = "mail.backends.LocalSMTPEmailBackend"
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)

Q_CLUSTER = {
    "name": os.environ.get("Q_CLUSTER_NAME", "decopaint"),
    "workers": int(os.environ.get("Q_CLUSTER_WORKERS", "2")),
    "timeout": int(os.environ.get("Q_CLUSTER_TIMEOUT", "180")),
    "retry": int(os.environ.get("Q_CLUSTER_RETRY", "240")),
    "orm": "default",
    "sync": env_bool("Q_CLUSTER_SYNC", DEBUG),
}

PK_PAYTRAIL_API_URL = os.environ.get(
    "PK_PAYTRAIL_API_URL", "https://services.paytrail.com/payments"
)
PK_PAYTRAIL_REDIRECT_SUCCESS_URL = os.environ.get(
    "PK_PAYTRAIL_REDIRECT_SUCCESS_URL", ""
)
PK_PAYTRAIL_REDIRECT_CANCEL_URL = os.environ.get(
    "PK_PAYTRAIL_REDIRECT_CANCEL_URL", ""
)
PK_PAYTRAIL_MERCHANT_ID = os.environ.get("PK_PAYTRAIL_MERCHANT_ID", "")
PK_PAYTRAIL_MERCHANT_SECRET = os.environ.get("PK_PAYTRAIL_MERCHANT_SECRET", "")
PK_PAYTRAIL_CURRENCY = os.environ.get("PK_PAYTRAIL_CURRENCY", "EUR")
PK_PAYTRAIL_LANGUAGE = os.environ.get("PK_PAYTRAIL_LANGUAGE", "FI")

MERCHANT_SYNC_ENABLED = env_bool("MERCHANT_SYNC_ENABLED", False)
GOOGLE_MERCHANT_CENTER_ID = os.environ.get("GOOGLE_MERCHANT_CENTER_ID", "5351296674")
GOOGLE_CUSTOMER_REVIEWS_ENABLED = env_bool("GOOGLE_CUSTOMER_REVIEWS_ENABLED", False)
GOOGLE_CUSTOMER_REVIEWS_DELIVERY_DAYS = int(
    os.environ.get("GOOGLE_CUSTOMER_REVIEWS_DELIVERY_DAYS", "4")
)

ANALYTICS_ENABLED = env_bool("ANALYTICS_ENABLED", False)
GA4_MEASUREMENT_ID = os.environ.get("GA4_MEASUREMENT_ID", "")
ANALYTICS_USER_ID_SALT = os.environ.get("ANALYTICS_USER_ID_SALT", SECRET_KEY)
MAPBOX_PUBLIC_TOKEN = os.environ.get("MAPBOX_PUBLIC_TOKEN", "")

PAYMENT_DEBUG_LOGGING = env_bool("PAYMENT_DEBUG_LOGGING", False)

SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", not DEBUG)
SECURE_HSTS_SECONDS = int(os.environ.get("SECURE_HSTS_SECONDS", "0"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", False)
SECURE_HSTS_PRELOAD = env_bool("SECURE_HSTS_PRELOAD", False)
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
X_FRAME_OPTIONS = "DENY"
