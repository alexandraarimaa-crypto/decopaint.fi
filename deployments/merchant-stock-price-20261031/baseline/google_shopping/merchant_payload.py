"""Pure helpers for converting legacy Content API products to Merchant API v1."""

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


_ENUM_FIELDS = {
    "availability": {
        "in stock": "IN_STOCK",
        "out of stock": "OUT_OF_STOCK",
        "preorder": "PREORDER",
        "backorder": "BACKORDER",
    },
    "condition": {
        "new": "NEW",
        "used": "USED",
        "refurbished": "REFURBISHED",
    },
    "pickupMethod": {
        "buy": "BUY",
        "reserve": "RESERVE",
        "not supported": "NOT_SUPPORTED",
    },
    "pickupSla": {
        "same day": "SAME_DAY",
        "same_day": "SAME_DAY",
        "next day": "NEXT_DAY",
        "next_day": "NEXT_DAY",
        "2-day": "TWO_DAY",
        "two day": "TWO_DAY",
        "two_day": "TWO_DAY",
        "3-day": "THREE_DAY",
        "three day": "THREE_DAY",
        "three_day": "THREE_DAY",
        "4-day": "FOUR_DAY",
        "four day": "FOUR_DAY",
        "four_day": "FOUR_DAY",
        "5-day": "FIVE_DAY",
        "five day": "FIVE_DAY",
        "five_day": "FIVE_DAY",
        "6-day": "SIX_DAY",
        "six day": "SIX_DAY",
        "six_day": "SIX_DAY",
        "multi-week": "MULTI_WEEK",
        "multi_week": "MULTI_WEEK",
    },
}


_DIRECT_ATTRIBUTE_FIELDS = (
    "title",
    "description",
    "link",
    "mobileLink",
    "imageLink",
    "additionalImageLinks",
    "brand",
    "gtins",
    "mpn",
    "identifierExists",
    "adult",
    "multipack",
    "isBundle",
    "ageGroup",
    "color",
    "gender",
    "material",
    "pattern",
    "sizes",
    "sizeSystem",
    "itemGroupId",
    "productTypes",
    "googleProductCategory",
    "shippingLabel",
    "shippingWeight",
    "availabilityDate",
    "expirationDate",
    "salePriceEffectiveDate",
    "includedDestinations",
    "excludedDestinations",
    "customLabel0",
    "customLabel1",
    "customLabel2",
    "customLabel3",
    "customLabel4",
)


def money_to_v1(value):
    """Convert Content API {value, currency} money to Merchant API Money."""
    if not value:
        return None
    amount = value.get("value")
    currency = value.get("currency") or value.get("currencyCode")
    if amount in (None, "") or not currency:
        return None
    try:
        micros = (Decimal(str(amount)) * Decimal("1000000")).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        )
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError("Invalid product price")
    return {"amountMicros": str(int(micros)), "currencyCode": str(currency).upper()}


def _enum_value(field, value):
    if value in (None, ""):
        return None
    text = str(value).strip()
    if text.isupper():
        return text
    return _ENUM_FIELDS[field].get(text.lower(), text.upper().replace(" ", "_"))


def legacy_to_product_input(product):
    """Build a Merchant API v1 ProductInput from a Content API-style mapping."""
    offer_id = str(product.get("offerId") or "").strip()
    if not offer_id:
        raise ValueError("offerId is required")

    attributes = {}
    for field in _DIRECT_ATTRIBUTE_FIELDS:
        value = product.get(field)
        if value not in (None, "", []):
            attributes[field] = value

    # Content API sometimes returns one GTIN while Merchant API v1 expects a list.
    if product.get("gtin") and not attributes.get("gtins"):
        attributes["gtins"] = [product["gtin"]]

    # Merchant API v1 renamed the singular Content API field to a repeated enum.
    if product.get("sizeType") and not attributes.get("sizeTypes"):
        size_type = str(product["sizeType"]).strip().upper().replace(" ", "_")
        attributes["sizeTypes"] = [size_type]

    for field in _ENUM_FIELDS:
        value = _enum_value(field, product.get(field))
        if value:
            attributes[field] = value

    for legacy_field, v1_field in (("price", "price"), ("salePrice", "salePrice")):
        value = money_to_v1(product.get(legacy_field))
        if value:
            attributes[v1_field] = value

    return {
        "offerId": offer_id,
        "contentLanguage": str(product.get("contentLanguage") or "fi").lower(),
        "feedLabel": str(product.get("feedLabel") or product.get("targetCountry") or "FI").upper(),
        "productAttributes": attributes,
    }


def product_input_id(offer_id, content_language="fi", feed_label="FI"):
    """Return the stable REST product input ID used by Merchant API v1."""
    return f"{str(content_language).lower()}~{str(feed_label).upper()}~{offer_id}"
