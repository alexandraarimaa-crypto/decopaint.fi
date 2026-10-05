# shop/context_processors.py
from django.conf import settings

from .models import StoreSettings

def store_settings(request):
    return {
        'store_settings': StoreSettings.get_settings(),
        'mapbox_public_token': settings.MAPBOX_PUBLIC_TOKEN,
    }
