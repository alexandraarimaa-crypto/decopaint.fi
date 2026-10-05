#!/usr/bin/env python3
"""
Create a secret-free Django settings module for the isolated staging site.

The source settings file is parsed as Python and sensitive top-level
assignments are removed before safe staging overrides are appended.
"""

import argparse
import ast
from pathlib import Path


SENSITIVE_NAMES = {
    "SECRET_KEY",
    "DEBUG",
    "ALLOWED_HOSTS",
    "CSRF_TRUSTED_ORIGINS",
    "DATABASES",
    "DEFAULT_FROM_EMAIL",
    "EMAIL_BACKEND",
    "EMAIL_HOST",
    "EMAIL_PORT",
    "EMAIL_USE_SSL",
    "EMAIL_USE_TLS",
    "EMAIL_HOST_USER",
    "EMAIL_HOST_PASSWORD",
    "SENDGRID_API_KEY",
    "PK_PAYTRAIL_API_URL",
    "PK_PAYTRAIL_REDIRECT_SUCCESS_URL",
    "PK_PAYTRAIL_REDIRECT_CANCEL_URL",
    "PK_PAYTRAIL_MERCHANT_ID",
    "PK_PAYTRAIL_MERCHANT_SECRET",
    "PK_PAYTRAIL_CURRENCY",
    "PK_PAYTRAIL_LANGUAGE",
    "STATIC_URL",
    "STATIC_ROOT",
    "MEDIA_URL",
    "MEDIA_ROOT",
    "CACHES",
    "SESSION_ENGINE",
    "SESSION_COOKIE_NAME",
    "SESSION_COOKIE_DOMAIN",
    "CSRF_COOKIE_NAME",
    "CSRF_COOKIE_DOMAIN",
    "Q_CLUSTER",
    "LOGGING",
    "MERCHANT_SYNC_ENABLED",
    "PAYMENT_DEBUG_LOGGING",
    "ANALYTICS_ENABLED",
    "GA4_MEASUREMENT_ID",
    "ANALYTICS_USER_ID_SALT",
    "SECURE_SSL_REDIRECT",
    "SECURE_PROXY_SSL_HEADER",
    "SECURE_HSTS_SECONDS",
    "SECURE_HSTS_INCLUDE_SUBDOMAINS",
    "SECURE_HSTS_PRELOAD",
    "SESSION_COOKIE_SECURE",
    "CSRF_COOKIE_SECURE",
}


def assigned_names(node):
    if isinstance(node, ast.Assign):
        names = []
        for target in node.targets:
            if isinstance(target, ast.Name):
                names.append(target.id)
        return names
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        return [node.target.id]
    return []


def sanitize(source):
    tree = ast.parse(source)
    tree.body = [
        node
        for node in tree.body
        if not (set(assigned_names(node)) & SENSITIVE_NAMES)
    ]
    ast.fix_missing_locations(tree)
    return ast.unparse(tree)


def staging_overrides(secret_file, database_file):
    return f'''

# --- Isolated staging overrides ---
from pathlib import Path as _StagingPath

STAGING = True
SECRET_KEY = _StagingPath({str(secret_file)!r}).read_text(encoding="utf-8").strip()
DEBUG = False
ALLOWED_HOSTS = ["develop.decopaint.fi", "localhost", "127.0.0.1"]
CSRF_TRUSTED_ORIGINS = ["https://develop.decopaint.fi"]

DATABASES = {{
    "default": {{
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": {str(database_file)!r},
    }}
}}

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
DEFAULT_FROM_EMAIL = "staging@invalid.example"

PK_PAYTRAIL_API_URL = "https://services.paytrail.com/payments"
PK_PAYTRAIL_REDIRECT_SUCCESS_URL = "https://develop.decopaint.fi/order/payment_success/"
PK_PAYTRAIL_REDIRECT_CANCEL_URL = "https://develop.decopaint.fi/order/payment_cancel/"
PK_PAYTRAIL_MERCHANT_ID = "staging-disabled"
PK_PAYTRAIL_MERCHANT_SECRET = "staging-disabled"
PK_PAYTRAIL_CURRENCY = "EUR"
PK_PAYTRAIL_LANGUAGE = "FI"

MERCHANT_SYNC_ENABLED = False
PAYMENT_DEBUG_LOGGING = False
ANALYTICS_ENABLED = False
GA4_MEASUREMENT_ID = ""
ANALYTICS_USER_ID_SALT = "staging-disabled"

STATIC_URL = "/static/"
STATIC_ROOT = str(_StagingPath(BASE_DIR) / "static")
MEDIA_URL = "https://decopaint.fi/media/"

CACHES = {{
    "default": {{
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "decopaint-staging",
    }}
}}
SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_NAME = "decopaint_staging_session"
CSRF_COOKIE_NAME = "decopaint_staging_csrf"
SESSION_COOKIE_DOMAIN = None
CSRF_COOKIE_DOMAIN = None

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

Q_CLUSTER = {{
    "name": "decopaint-staging",
    "sync": True,
    "workers": 1,
    "timeout": 60,
}}

LOGGING = {{
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {{
        "console": {{"class": "logging.StreamHandler"}},
    }},
    "root": {{
        "handlers": ["console"],
        "level": "WARNING",
    }},
}}
'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source")
    parser.add_argument("target")
    parser.add_argument("--secret-file", required=True)
    parser.add_argument("--database-file", required=True)
    args = parser.parse_args()

    source_path = Path(args.source)
    target_path = Path(args.target)
    secret_file = Path(args.secret_file)
    database_file = Path(args.database_file)

    sanitized = sanitize(source_path.read_text(encoding="utf-8"))
    target_path.write_text(
        sanitized + staging_overrides(secret_file, database_file),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
