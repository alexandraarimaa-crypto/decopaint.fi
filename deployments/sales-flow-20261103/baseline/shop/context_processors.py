# shop/context_processors.py
from .models import StoreSettings

def store_settings(request):
    settings = StoreSettings.get_settings()
    match = getattr(request, 'resolver_match', None)
    route_name = match.url_name if match and match.namespace == 'shop' else ''
    is_contact_page = bool(
        route_name == 'contact'
    )
    return {
        'store_settings': settings,
        # Mapbox is used only on the contact page.  Avoid making every shop,
        # cart, blog and service page wait for its stylesheet.
        'needs_mapbox': is_contact_page,
        # Product galleries and catalogue sliders are not needed on ordinary
        # content pages.  Keep their CSS limited to the views that use it.
        'needs_lightgallery': route_name == 'product_detail',
        'needs_slick': route_name in {
            'product_detail',
            'product_list_by_category',
            'product_list_by_tag',
        },
    }
