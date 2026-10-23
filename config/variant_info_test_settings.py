"""Isolated admin/variant tests; no production database or integrations."""
from .test_settings import *  # noqa: F403

INSTALLED_APPS = [
    'admin_interface', 'colorfield', *INSTALLED_APPS,
    'django.contrib.admin.apps.SimpleAdminConfig',
]
LANGUAGES = [('fi', 'Suomi'), ('sv', 'Svenska'), ('en', 'English')]
