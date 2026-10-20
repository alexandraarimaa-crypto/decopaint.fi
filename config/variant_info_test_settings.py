"""Isolated admin/variant tests; no production database or integrations."""
from .test_settings import *  # noqa: F403

INSTALLED_APPS = [*INSTALLED_APPS, 'django.contrib.admin.apps.SimpleAdminConfig', 'django_admin_inline_paginator']
LANGUAGES = [('fi', 'Suomi'), ('sv', 'Svenska'), ('en', 'English')]
