"""Privacy-safe Google Analytics 4 ecommerce payload builders.

Only allowlisted commerce metadata is returned from this module. Customer
names, email addresses, phone numbers, postal addresses, notes and payment
provider transaction identifiers must never be added to these payloads.
"""

from datetime import timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import hashlib
import hmac
import re

from django.conf import settings
from django.db.models import Q
from django.utils import timezone


CURRENCY = "EUR"
BRAND = "OIKOS"
MAX_ITEMS = 200
MAX_TEXT_LENGTH = 100

_EMAIL_RE = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")
_PHONE_RE = re.compile(r"\+?\d[\d\s().-]{5,}\d")
_E164_PHONE_RE = re.compile(r"\+[1-9]\d{6,14}$")


def _redact_phone(match):
    candidate = match.group(0)
    has_phone_format = candidate.startswith("+") or any(
        separator in candidate for separator in (" ", "(", ")", ".", "-")
    )
    digits = sum(character.isdigit() for character in candidate)
    return "[redacted]" if has_phone_format and digits >= 7 else candidate


def _text(value, max_length=MAX_TEXT_LENGTH):
    """Return a bounded string with obvious contact data redacted."""
    text = " ".join(str(value or "").split())
    text = _EMAIL_RE.sub("[redacted]", text)
    text = _PHONE_RE.sub(_redact_phone, text)
    return text[:max_length]


def _money(value):
    try:
        decimal_value = Decimal(str(value or "0"))
    except (InvalidOperation, TypeError, ValueError):
        decimal_value = Decimal("0")
    return float(decimal_value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _category_name(product):
    if not product:
        return ""
    category_manager = getattr(product, "category", None)
    if not category_manager:
        return ""
    try:
        category = category_manager.first()
    except (AttributeError, TypeError):
        category = None
    return _text(getattr(category, "name", ""))


def _variant_name(variant):
    if not variant:
        return ""
    values = [
        getattr(variant, "size", ""),
        getattr(variant, "color", ""),
        getattr(variant, "grain", ""),
        getattr(variant, "gloss", ""),
        getattr(variant, "base", ""),
    ]
    return _text(" / ".join(str(value) for value in values if value))


def _item_id(product, variant=None):
    if variant:
        item_code = _text(getattr(variant, "item_code", ""))
        if item_code:
            return item_code
    sku = _text(getattr(product, "sku", ""))
    if sku:
        return sku
    product_id = getattr(product, "id", None)
    return f"product-{product_id}" if product_id is not None else "product"


def _item(product, *, variant=None, price=0, quantity=1):
    item = {
        "item_id": _item_id(product, variant),
        "item_name": _text(getattr(product, "name", "")) or "Product",
        "item_brand": BRAND,
        "price": _money(price),
        "quantity": max(int(quantity or 1), 1),
    }
    category = _category_name(product)
    variant_name = _variant_name(variant)
    if category:
        item["item_category"] = category
    if variant_name:
        item["item_variant"] = variant_name
    return item


def analytics_user_id(user):
    """Return a stable, opaque first-party ID for an authenticated user."""
    if not user or not getattr(user, "is_authenticated", False):
        return ""
    user_pk = getattr(user, "pk", None)
    if user_pk is None:
        return ""
    salt = getattr(settings, "ANALYTICS_USER_ID_SALT", settings.SECRET_KEY)
    digest = hmac.new(
        str(salt).encode("utf-8"),
        f"decopaint-ga4-user:{user_pk}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"dp_{digest[:32]}"


def analytics_user_context(user):
    user_id = analytics_user_id(user)
    if not user_id:
        return {"login_status": "guest"}
    return {
        "user_id": user_id,
        "login_status": "authenticated",
    }


def build_product_event(product, user=None):
    price_source = getattr(product, "total_price", 0) if product else 0
    price = price_source(user) if callable(price_source) else price_source
    item = _item(product, price=price)
    return {
        "name": "view_item",
        "params": {
            "currency": CURRENCY,
            "value": item["price"],
            "items": [item],
        },
    }


def _cart_items(cart):
    items = []
    for cart_item in cart:
        if len(items) >= MAX_ITEMS:
            break
        product_data = cart_item.get("product_data", {})
        variant_info = cart_item.get("variant_info", {})
        quantity = max(int(cart_item.get("quantity", 1) or 1), 1)
        price = variant_info.get("price", cart_item.get("price", 0))
        product = type(
            "AnalyticsProduct",
            (),
            {
                "id": product_data.get("id"),
                "name": product_data.get("name", ""),
                "sku": variant_info.get("item_code", ""),
                "category": None,
            },
        )()
        variant = type(
            "AnalyticsVariant",
            (),
            {
                "item_code": variant_info.get("item_code", ""),
                "size": variant_info.get("size", ""),
                "color": variant_info.get("color", ""),
                "grain": variant_info.get("grain", ""),
                "gloss": variant_info.get("gloss", ""),
                "base": variant_info.get("base", ""),
            },
        )()
        item = _item(product, variant=variant, price=price, quantity=quantity)
        family = _text(variant_info.get("family", ""))
        if family:
            item["item_category"] = family
        items.append(item)
    return items


def build_cart_params(cart):
    params = {
        "currency": CURRENCY,
        "value": _money(cart.get_total_price()),
        "items": _cart_items(cart),
    }
    coupon = getattr(cart, "coupon", None)
    coupon_code = _text(getattr(coupon, "code", ""))
    if coupon_code:
        params["coupon"] = coupon_code
    return params


def build_cart_event(cart, name):
    if name not in {
        "view_cart",
        "begin_checkout",
        "add_shipping_info",
        "add_payment_info",
    }:
        raise ValueError("Unsupported cart analytics event")
    return {"name": name, "params": build_cart_params(cart)}


def _order_customer_type(order):
    from order.models import Order

    identity = Q()
    if getattr(order, "user_id", None):
        identity |= Q(user_id=order.user_id)
    email = getattr(order, "email", "")
    if email:
        identity |= Q(email__iexact=email)
    if not identity:
        return "new"

    confirmed = Q(payed=True) | (
        Q(payment_method="cod") & ~Q(status="canceled")
    )
    return (
        "returning"
        if Order.objects.filter(identity & confirmed).exclude(pk=order.pk).exists()
        else "new"
    )


def build_purchase_event(order):
    items = []
    for order_item in order.items.select_related("variant__product").all()[:MAX_ITEMS]:
        variant = getattr(order_item, "variant", None)
        product = getattr(variant, "product", None) if variant else None
        quantity = max(int(getattr(order_item, "quantity", 1) or 1), 1)
        total_price = _money(getattr(order_item, "price", 0))
        unit_price = Decimal(str(total_price)) / Decimal(quantity)
        items.append(
            _item(
                product,
                variant=variant,
                price=unit_price,
                quantity=quantity,
            )
        )

    params = {
        "transaction_id": f"DP-{order.pk}",
        "currency": CURRENCY,
        "value": _money(order.get_total_price()),
        "tax": _money(order.get_total_tax()),
        "shipping": _money(order.get_delivery_price()),
        "payment_type": _text(order.payment_method),
        "shipping_tier": _text(order.shipping_method),
        "customer_type": _order_customer_type(order),
        "login_status": (
            "authenticated" if getattr(order, "user_id", None) else "guest"
        ),
        "items": items,
    }
    coupon_code = _text(getattr(getattr(order, "coupon", None), "code", ""))
    if coupon_code:
        params["coupon"] = coupon_code
    return {"name": "purchase", "params": params}


def build_google_ads_enhanced_conversion_data(order):
    """Build the separately handled Google Ads enhanced-conversion payload.

    This is deliberately not part of the GA4 ecommerce event: it contains
    customer-provided data and may only be sent by the browser after the
    visitor has granted ``ad_user_data`` consent. The Google tag normalizes
    and hashes supported fields before transmitting them to Google Ads.
    """
    email = " ".join(str(getattr(order, "email", "") or "").split()).lower()
    if not _EMAIL_RE.fullmatch(email):
        email = ""

    phone = "".join(str(getattr(order, "phone", "") or "").split())
    phone = re.sub(r"[().-]", "", phone)
    if not _E164_PHONE_RE.fullmatch(phone):
        phone = ""

    address = {
        "first_name": " ".join(
            str(getattr(order, "first_name", "") or "").split()
        ),
        "last_name": " ".join(
            str(getattr(order, "last_name", "") or "").split()
        ),
        "street": " ".join(
            str(getattr(order, "address", "") or "").split()
        ),
        "city": " ".join(str(getattr(order, "city", "") or "").split()),
        "postal_code": " ".join(
            str(getattr(order, "postal", "") or "").split()
        ),
    }
    address = {key: value for key, value in address.items() if value}
    if address:
        address["country"] = "FI"

    payload = {}
    if email:
        payload["email"] = email
    if phone:
        payload["phone_number"] = phone
    if address:
        payload["address"] = address
    return payload


def build_google_customer_reviews_data(order):
    """Return the consent-widget payload for a confirmed Google review invite.

    This payload intentionally contains only the fields Google Customer Reviews
    requires to offer its own post-purchase opt-in: an order reference, the
    buyer's email, country, estimated arrival date, and valid GTINs.  It is not
    sent to GA4 or included in any advertising event.
    """
    if not getattr(settings, "GOOGLE_CUSTOMER_REVIEWS_ENABLED", True):
        return {}

    merchant_id = str(
        getattr(settings, "GOOGLE_MERCHANT_CENTER_ID", "5351296674")
    ).strip()
    email = " ".join(str(getattr(order, "email", "") or "").split()).lower()
    order_id = getattr(order, "pk", None)
    if not merchant_id.isdigit() or not _EMAIL_RE.fullmatch(email) or order_id is None:
        return {}

    try:
        delivery_days = max(
            int(getattr(settings, "GOOGLE_CUSTOMER_REVIEWS_DELIVERY_DAYS", 4)),
            0,
        )
    except (TypeError, ValueError):
        delivery_days = 4
    if getattr(order, "shipping_method", "") == "pickup":
        delivery_days = 0

    products = []
    try:
        order_items = order.items.select_related("variant__product").all()[:MAX_ITEMS]
    except (AttributeError, TypeError):
        order_items = []

    for order_item in order_items:
        variant = getattr(order_item, "variant", None)
        barcode = getattr(order_item, "barcode", "") or getattr(variant, "barcode", "")
        gtin = re.sub(r"\D", "", str(barcode or ""))
        if len(gtin) in {8, 12, 13, 14}:
            products.append({"gtin": gtin})

    payload = {
        "merchant_id": int(merchant_id),
        "order_id": f"DP-{order_id}",
        "email": email,
        "delivery_country": "FI",
        "estimated_delivery_date": (
            timezone.localdate() + timedelta(days=delivery_days)
        ).isoformat(),
    }
    if products:
        payload["products"] = products
    return payload


def build_search_event(search_term, result_count):
    safe_term = _text(search_term)
    if not safe_term:
        return None
    return {
        "name": "view_search_results",
        "params": {
            "search_term": safe_term,
            "result_count": max(int(result_count or 0), 0),
        },
    }
