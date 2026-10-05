"""Source-grounded Open Graph and Product structured-data helpers.

The catalogue contains many variants whose prices and availability differ.  A
product-level Offer is therefore emitted only when the page has resolved the
same concrete variant that the visible price widget uses.
"""

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from html import unescape
import json
import re
from urllib.parse import urlencode

from django.utils.html import strip_tags


SCHEMA_CONTEXT = "https://schema.org"
SELECTION_KEYS = ("size", "color", "grain", "gloss", "base")


def clean_text(value):
    """Return compact plain text suitable for metadata and JSON-LD."""

    return re.sub(r"\s+", " ", unescape(strip_tags(str(value or "")))).strip()


def absolute_product_image(request, product):
    """Return the first usable product image as an absolute HTTPS URL."""

    for field_name in ("thumbnail", "image"):
        field = getattr(product, field_name, None)
        if not field:
            continue
        try:
            url = field.url
        except (AttributeError, ValueError):
            continue
        if url:
            return request.build_absolute_uri(url)
    return ""


def selected_offer_url(canonical_url, selection):
    """Build a shareable URL containing only product-option parameters."""

    selected = [
        (key, str(selection.get(key, "")).strip())
        for key in SELECTION_KEYS
        if str(selection.get(key, "")).strip()
    ]
    return f"{canonical_url}?{urlencode(selected)}" if selected else canonical_url


def _public_price(variant):
    try:
        value = Decimal(str(variant.total_price(None)))
    except (InvalidOperation, TypeError, ValueError):
        return None
    if not value.is_finite() or value <= 0:
        return None
    return format(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), "f")


def build_product_data(
    *,
    request,
    product,
    name,
    description,
    canonical_url,
    variant=None,
    selection=None,
):
    """Build accurate Product data and optional resolved-variant Offer."""

    image_url = absolute_product_image(request, product)
    data = {
        "@context": SCHEMA_CONTEXT,
        "@type": "Product",
        "name": clean_text(name),
        "description": clean_text(description),
        "url": canonical_url,
        "brand": {"@type": "Brand", "name": "OIKOS"},
    }
    if image_url:
        data["image"] = [image_url]

    product_sku = clean_text(getattr(product, "sku", ""))
    if product_sku:
        data["sku"] = product_sku

    if variant is not None:
        price = _public_price(variant)
        if price is not None:
            variant_sku = clean_text(getattr(variant, "item_code", ""))
            offer = {
                "@type": "Offer",
                "priceCurrency": "EUR",
                "price": price,
                "availability": (
                    f"{SCHEMA_CONTEXT}/PreOrder"
                    if bool(getattr(variant, "order_item", False))
                    else f"{SCHEMA_CONTEXT}/InStock"
                ),
                "itemCondition": f"{SCHEMA_CONTEXT}/NewCondition",
                "url": selected_offer_url(canonical_url, selection or {}),
                "seller": {"@type": "Organization", "name": "Deco Paint Finland Oy"},
            }
            if variant_sku:
                offer["sku"] = variant_sku
            data["offers"] = offer

    return data


def json_for_script(data):
    """Serialize JSON-LD without allowing user content to close the script."""

    return (
        json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        .replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
    )
