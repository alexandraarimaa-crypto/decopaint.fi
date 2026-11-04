"""Consent-aware capture of analytics and Google Ads attribution for an order."""
from __future__ import annotations

import json
import os
import re
from datetime import timedelta
from urllib.parse import unquote

from django.conf import settings
from django.utils import timezone
from django.utils.dateparse import parse_datetime

ATTRIBUTION_COOKIE = "dp_attribution"
DEFAULT_MEASUREMENT_ID = "G-HXEJKEB3MW"
_CLICK_ID_RE = re.compile(r"^[A-Za-z0-9._~-]{1,256}$")
_GA_COOKIE_RE = re.compile(r"^[A-Za-z0-9._$~-]{1,512}$")
_MAX_CLICK_AGE = timedelta(days=90)


def _load_cookie_json(request, name):
    raw_value = request.COOKIES.get(name, "")
    if not raw_value:
        return {}
    try:
        value = json.loads(unquote(raw_value))
    except (TypeError, ValueError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _clean_text(value, max_length):
    if not isinstance(value, str):
        return ""
    return value.strip()[:max_length]


def _clean_click_id(value):
    value = _clean_text(value, 256)
    return value if _CLICK_ID_RE.fullmatch(value) else ""


def _clean_ga_cookie(value):
    value = _clean_text(value, 512)
    return value if _GA_COOKIE_RE.fullmatch(value) else ""


def _session_cookie_name():
    measurement_id = str(
        getattr(settings, "GA4_MEASUREMENT_ID", "")
        or os.environ.get("GA4_MEASUREMENT_ID", DEFAULT_MEASUREMENT_ID)
    ).strip()
    return "_ga_" + re.sub(r"[^A-Za-z0-9]", "", measurement_id.removeprefix("G-"))


def extract_order_attribution(request):
    """Return validated consent, Analytics cookies, and ad attribution."""
    consent_settings = _load_cookie_json(request, "cookie_settings")
    analytics_storage = consent_settings.get("analytics_storage")
    ad_storage = consent_settings.get("ad_storage")
    ad_user_data = consent_settings.get("ad_user_data")
    ad_personalization = consent_settings.get("ad_personalization")

    if analytics_storage == "granted":
        analytics_consent = "granted"
    elif analytics_storage == "denied":
        analytics_consent = "denied"
    else:
        analytics_consent = "unknown"

    if ad_storage == "granted" and ad_user_data == "granted":
        ads_consent = "granted"
    elif ad_storage == "denied" or ad_user_data == "denied":
        ads_consent = "denied"
    else:
        ads_consent = "unknown"

    result = {
        "analytics_consent": analytics_consent,
        "ads_consent": ads_consent,
        "ads_personalization_consent": (
            ad_personalization
            if ad_personalization in {"granted", "denied"}
            else "unknown"
        ),
    }
    if analytics_consent == "granted":
        result.update({
            "ga_client_id": _clean_ga_cookie(request.COOKIES.get("_ga", "")),
            "ga_session_id": _clean_ga_cookie(
                request.COOKIES.get(_session_cookie_name(), "")
            ),
        })

    if ads_consent != "granted":
        return result

    attribution = _load_cookie_json(request, ATTRIBUTION_COOKIE)
    if not attribution:
        return result
    captured_at = parse_datetime(_clean_text(attribution.get("captured_at"), 64))
    if captured_at is None:
        return result
    if timezone.is_naive(captured_at):
        captured_at = timezone.make_aware(
            captured_at, timezone.get_current_timezone()
        )
    now = timezone.now()
    if captured_at > now + timedelta(minutes=5) or now - captured_at > _MAX_CLICK_AGE:
        return result

    result.update({
        "gclid": _clean_click_id(attribution.get("gclid")),
        "gbraid": _clean_click_id(attribution.get("gbraid")),
        "wbraid": _clean_click_id(attribution.get("wbraid")),
        "utm_source": _clean_text(attribution.get("utm_source"), 255),
        "utm_medium": _clean_text(attribution.get("utm_medium"), 255),
        "utm_campaign": _clean_text(attribution.get("utm_campaign"), 255),
        "utm_term": _clean_text(attribution.get("utm_term"), 255),
        "utm_content": _clean_text(attribution.get("utm_content"), 255),
        "ads_landing_page": _clean_text(attribution.get("landing_page"), 500),
        "ads_click_captured_at": captured_at,
    })
    return result


def apply_order_attribution(order, request):
    """Copy validated consent and attribution fields onto an unsaved order."""
    for field, value in extract_order_attribution(request).items():
        setattr(order, field, value)
    return order
