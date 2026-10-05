"""Choose the storefront's initial language from the visitor's country."""

from __future__ import annotations

import ipaddress
import re
from bisect import bisect_right
from functools import lru_cache
from pathlib import Path

from django.conf import settings
from django.utils.translation import activate


_DATA_DIR = Path(__file__).resolve().parent / "data" / "country_ip"
_SEARCH_CRAWLER = re.compile(
    r"(?:adsbot-google|bingbot|googlebot|google-inspectiontool|storebot-google)",
    re.IGNORECASE,
)
_COUNTRY_HEADERS = (
    "HTTP_CF_IPCOUNTRY",
    "HTTP_X_COUNTRY_CODE",
    "HTTP_X_GEOIP_COUNTRY",
    "GEOIP_COUNTRY_CODE",
    "IP2LOCATION_COUNTRY_SHORT",
)


def _load_ranges(version: int):
    ranges = []
    for country in ("fi", "se"):
        path = _DATA_DIR / f"{country}-ipv{version}.cidr"
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for line in lines:
            value = line.strip()
            if not value or value.startswith("#"):
                continue
            network = ipaddress.ip_network(value)
            ranges.append((int(network.network_address), int(network.broadcast_address), country))
    ranges.sort(key=lambda row: row[0])
    return tuple(row[0] for row in ranges), tuple(ranges)


_IPV4_STARTS, _IPV4_RANGES = _load_ranges(4)
_IPV6_STARTS, _IPV6_RANGES = _load_ranges(6)


def _parse_ip(value):
    if not value:
        return None
    candidate = str(value).strip()
    if candidate.startswith("[") and "]" in candidate:
        candidate = candidate[1:candidate.index("]")]
    elif candidate.count(":") == 1 and "." in candidate:
        candidate = candidate.split(":", 1)[0]
    try:
        return ipaddress.ip_address(candidate)
    except ValueError:
        return None


def _client_ip(request):
    direct = _parse_ip(request.META.get("REMOTE_ADDR"))
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded and (direct is None or not direct.is_global):
        for value in forwarded.split(","):
            candidate = _parse_ip(value)
            if candidate is not None and candidate.is_global:
                return candidate
    return direct


@lru_cache(maxsize=8192)
def _country_for_ip(value):
    address = _parse_ip(value)
    if address is None:
        return None
    starts, ranges = (
        (_IPV4_STARTS, _IPV4_RANGES)
        if address.version == 4
        else (_IPV6_STARTS, _IPV6_RANGES)
    )
    index = bisect_right(starts, int(address)) - 1
    if index >= 0:
        start, end, country = ranges[index]
        if start <= int(address) <= end:
            return country
    return "other" if address.is_global else None


def _country_from_request(request):
    for header in _COUNTRY_HEADERS:
        value = request.META.get(header)
        if value:
            return str(value).strip().lower()
    address = _client_ip(request)
    return _country_for_ip(str(address)) if address is not None else None


def _default_language(request):
    user_agent = request.META.get("HTTP_USER_AGENT", "")
    if _SEARCH_CRAWLER.search(user_agent):
        return settings.LANGUAGE_CODE
    country = _country_from_request(request)
    if country == "fi":
        return "fi"
    if country == "se":
        return "sv"
    if country is not None:
        return "en"
    return settings.LANGUAGE_CODE


class CountryDefaultLanguageMiddleware:
    """Apply country defaults without overriding a customer's manual choice."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        available = {code for code, _name in settings.LANGUAGES}
        cookie_name = settings.LANGUAGE_COOKIE_NAME
        explicit = request.COOKIES.get(cookie_name)
        if not explicit and hasattr(request, "session"):
            explicit = request.session.get(cookie_name)

        language = explicit if explicit in available else _default_language(request)
        if language not in available:
            language = settings.LANGUAGE_CODE
        activate(language)
        request.LANGUAGE_CODE = language
        return self.get_response(request)
