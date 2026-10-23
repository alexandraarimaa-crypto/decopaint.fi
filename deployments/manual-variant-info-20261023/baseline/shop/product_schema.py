"""Source-grounded Open Graph and Product structured-data helpers.

The catalogue contains many variants whose prices and availability differ.  A
product-level Offer is therefore emitted only when the page has resolved the
same concrete variant that the visible price widget uses.
"""

from datetime import timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from html import unescape
import json
import re
from urllib.parse import urlencode

from django.db.models import Avg
from django.utils import timezone
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
        # Structured data must always expose the public storefront price.
        # Never personalize it with an authenticated B2B customer's group.
        value = Decimal(str(variant.total_price(None)))
    except (InvalidOperation, TypeError, ValueError):
        return None
    if not value.is_finite() or value <= 0:
        return None
    return format(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), "f")


def merchant_return_policy():
    """Return the published Deco Paint Finland consumer return policy.

    The policy page limits sales to Finland and gives consumers 14 days from
    receipt to return an unused, fault-free item.  It provides a postal-return
    route and states that ordinary postal returns are free.  Exceptional goods
    requiring special transport remain subject to the separately published
    case-by-case terms.
    """

    return {
        "@type": "MerchantReturnPolicy",
        "applicableCountry": "FI",
        "returnPolicyCategory": (
            f"{SCHEMA_CONTEXT}/MerchantReturnFiniteReturnWindow"
        ),
        "merchantReturnDays": 14,
        "returnMethod": f"{SCHEMA_CONTEXT}/ReturnByMail",
        "returnFees": f"{SCHEMA_CONTEXT}/FreeReturn",
    }


def preorder_availability_date():
    """Return the conservative public availability estimate for order items."""

    estimated = timezone.localtime(timezone.now()) + timedelta(days=28)
    return estimated.replace(hour=9, minute=0, second=0, microsecond=0).isoformat(
        timespec="minutes"
    )


def offer_shipping_details(*, order_item=False):
    """Return the published Finnish delivery choices for a product offer.

    The terms show €8.90 collection-point and €14.90 home delivery.  They
    promise dispatch in 1–3 business days, and the storefront publishes a
    1–3-business-day delivery window for stock products.  Both intervals are
    represented explicitly so Google can evaluate the complete delivery time.
    """

    # Stock products are shown as 1-3-day deliveries.  Made-to-order products
    # are shown as 2-4 weeks on the same landing page.  Keep Google's total
    # handling + transit window aligned with those customer-facing promises.
    if order_item:
        handling_min, handling_max = 11, 25
        transit_min, transit_max = 1, 3
    else:
        handling_min, handling_max = 0, 1
        transit_min, transit_max = 1, 2

    details = []
    for rate in ("8.90", "14.90"):
        details.append(
            {
                "@type": "OfferShippingDetails",
                "shippingDestination": {
                    "@type": "DefinedRegion",
                    "addressCountry": "FI",
                },
                "shippingRate": {
                    "@type": "MonetaryAmount",
                    "value": rate,
                    "currency": "EUR",
                },
                "deliveryTime": {
                    "@type": "ShippingDeliveryTime",
                    "handlingTime": {
                        "@type": "QuantitativeValue",
                        "minValue": handling_min,
                        "maxValue": handling_max,
                        "unitCode": "DAY",
                    },
                    "transitTime": {
                        "@type": "QuantitativeValue",
                        "minValue": transit_min,
                        "maxValue": transit_max,
                        "unitCode": "DAY",
                    },
                },
            }
        )
    return details


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
            is_order_item = bool(getattr(variant, "order_item", False))
            offer = {
                "@type": "Offer",
                "priceCurrency": "EUR",
                "price": price,
                "availability": (
                    f"{SCHEMA_CONTEXT}/PreOrder"
                    if is_order_item
                    else f"{SCHEMA_CONTEXT}/InStock"
                ),
                "itemCondition": f"{SCHEMA_CONTEXT}/NewCondition",
                "url": selected_offer_url(canonical_url, selection or {}),
                "seller": {"@type": "Organization", "name": "Deco Paint Finland Oy"},
                "hasMerchantReturnPolicy": merchant_return_policy(),
                "shippingDetails": offer_shipping_details(
                    order_item=is_order_item
                ),
            }
            if is_order_item:
                offer["availabilityStarts"] = preorder_availability_date()
            if variant_sku:
                offer["sku"] = variant_sku
            data["offers"] = offer

    # Publish only moderated, real customer reviews. Unapproved submissions
    # must never be exposed as Product review markup.
    active_reviews = product.reviews.filter(active=True).order_by("-created")
    review_count = active_reviews.count()
    if review_count:
        average_rating = active_reviews.aggregate(value=Avg("rating"))["value"]
        if average_rating is not None:
            data["aggregateRating"] = {
                "@type": "AggregateRating",
                "ratingValue": format(
                    Decimal(str(average_rating)).quantize(
                        Decimal("0.1"), rounding=ROUND_HALF_UP
                    ),
                    "f",
                ),
                "reviewCount": review_count,
                "bestRating": 5,
                "worstRating": 1,
            }

        review_items = []
        for review in active_reviews[:5]:
            item = {
                "@type": "Review",
                "author": {
                    "@type": "Person",
                    "name": clean_text(review.name) or "Vahvistettu asiakas",
                },
                "datePublished": review.created.date().isoformat(),
                "reviewRating": {
                    "@type": "Rating",
                    "ratingValue": int(review.rating),
                    "bestRating": 5,
                    "worstRating": 1,
                },
                "reviewBody": clean_text(review.text),
            }
            title = clean_text(review.title)
            if title:
                item["name"] = title
            review_items.append(item)
        if review_items:
            data["review"] = review_items

    return data


def json_for_script(data):
    """Serialize JSON-LD without allowing user content to close the script."""

    return (
        json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        .replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
    )
