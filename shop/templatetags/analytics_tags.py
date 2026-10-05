from django import template
from django.conf import settings

from shop.analytics import analytics_user_context


register = template.Library()


@register.simple_tag(takes_context=True)
def analytics_config(context):
    request = context.get("request")
    user = getattr(request, "user", None)
    return {
        "enabled": getattr(settings, "ANALYTICS_ENABLED", True),
        "measurement_id": getattr(
            settings,
            "GA4_MEASUREMENT_ID",
            "G-HXEJKEB3MW",
        ),
        "google_ads_id": getattr(
            settings,
            "GOOGLE_ADS_ID",
            "AW-392845597",
        ),
        "user": analytics_user_context(user),
    }
