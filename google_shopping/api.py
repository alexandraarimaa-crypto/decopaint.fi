"""Merchant API integration for Deco Paint's product catalogue.

The previous implementation used the deprecated Content API for Shopping.
Merchant API keeps the same OAuth scope, but uses product inputs, an explicit
data source, and different resource names.  This module deliberately uses the
REST interface through ``google-auth`` so it does not add a gRPC dependency to
the deployment.
"""

import base64
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import logging
import os

from google.auth.transport.requests import AuthorizedSession
from google.oauth2.service_account import Credentials
from shop.models import Category, Variant


logger = logging.getLogger(__name__)

SERVICE_ACCOUNT_FILE = os.path.join(os.path.dirname(__file__), "client_secret.json")
SCOPES = ["https://www.googleapis.com/auth/content"]
MERCHANT_ID = "5351296674"
MERCHANT_API_BASE_URL = "https://merchantapi.googleapis.com"
PRODUCTS_API_VERSION = "v1"

# This is the existing Content API source in Merchant Center.  Google documents
# that Content API sources are compatible with Merchant API.  An environment
# variable permits a future dedicated Merchant API source without a code change.
DEFAULT_DATA_SOURCE_ID = "10433825709"


class MerchantApiError(RuntimeError):
    """A failed Merchant API request with a safe, actionable error message."""

    def __init__(self, status_code, message):
        self.status_code = status_code
        super().__init__(message)


class MerchantApiNotFound(MerchantApiError):
    """Raised only when a requested Merchant resource does not exist."""


def _configured_data_source_name(merchant_id):
    configured = os.environ.get("MERCHANT_API_DATA_SOURCE", "").strip()
    if configured:
        if not configured.startswith(f"accounts/{merchant_id}/dataSources/"):
            raise ValueError(
                "MERCHANT_API_DATA_SOURCE must use the format "
                f"accounts/{merchant_id}/dataSources/{{data_source_id}}."
            )
        return configured

    data_source_id = os.environ.get(
        "MERCHANT_API_DATA_SOURCE_ID", DEFAULT_DATA_SOURCE_ID
    ).strip()
    if not data_source_id:
        raise ValueError("MERCHANT_API_DATA_SOURCE_ID must not be empty.")
    return f"accounts/{merchant_id}/dataSources/{data_source_id}"


def _normalise_api_error(response):
    """Return a compact error message without writing response bodies to logs."""
    try:
        payload = response.json()
    except ValueError:
        payload = {}

    details = payload.get("error", {}) if isinstance(payload, dict) else {}
    message = details.get("message") or f"HTTP {response.status_code}"
    if response.status_code == 403:
        message = (
            f"Merchant API permission denied: {message}. Ensure the Merchant "
            "Center account is registered to the Google Cloud project used by "
            "this service account."
        )
    return message


def _normalise_enum(value, mapping):
    text = str(value or "").strip()
    return mapping.get(text.lower(), text.upper())


def _price_to_merchant_api(value):
    """Convert a Content API price to the Merchant API micros representation."""
    if not isinstance(value, dict):
        return None

    amount = value.get("value", value.get("amount"))
    currency = value.get("currency", value.get("currencyCode"))
    try:
        decimal_amount = Decimal(str(amount))
    except (InvalidOperation, TypeError, ValueError):
        return None
    if not currency:
        return None

    micros = (decimal_amount * Decimal("1000000")).quantize(
        Decimal("1"), rounding=ROUND_HALF_UP
    )
    return {
        "amountMicros": str(int(micros)),
        "currencyCode": str(currency).upper(),
    }


def normalize_product_data_for_merchant_api(product_data):
    """Normalise legacy spelling before translating a catalogue payload.

    A few older admin paths still use the feed-style pickup keys.  Merchant
    API accepts the camel-case product attribute names, while ``storeCode`` is
    local-inventory data and must never be sent with an online product input.
    """
    normalized = dict(product_data)
    if "pickup_method" in normalized:
        normalized.setdefault("pickupMethod", normalized.pop("pickup_method"))
    if "pickup_SLA" in normalized:
        normalized.setdefault("pickupSla", normalized.pop("pickup_SLA"))
    normalized.pop("storeCode", None)
    return normalized


def build_merchant_product_input(product_data):
    """Translate the legacy product dictionary into a Merchant API input.

    Product attributes moved under ``productAttributes`` in Merchant API, and
    price values are represented in micros.  Keeping this conversion in one
    place makes all existing catalogue tasks use the new API consistently.
    """
    data = normalize_product_data_for_merchant_api(product_data)
    offer_id = str(data.get("offerId", "")).strip()
    content_language = str(data.get("contentLanguage", "fi")).lower()
    feed_label = str(data.get("feedLabel") or data.get("targetCountry") or "FI").upper()
    if not offer_id:
        raise ValueError("Merchant product payload must contain offerId.")

    attributes = {}
    for field in (
        "title",
        "description",
        "link",
        "imageLink",
        "additionalImageLinks",
        "brand",
        "googleProductCategory",
        "productTypes",
        "gtins",
        "mpn",
        "identifierExists",
    ):
        value = data.get(field)
        if value not in (None, "", [], {}):
            attributes[field] = value

    availability = _normalise_enum(
        data.get("availability"),
        {
            "in stock": "IN_STOCK",
            "out of stock": "OUT_OF_STOCK",
            "preorder": "PREORDER",
            "backorder": "BACKORDER",
        },
    )
    if availability:
        attributes["availability"] = availability

    condition = _normalise_enum(
        data.get("condition"),
        {"new": "NEW", "used": "USED", "refurbished": "REFURBISHED"},
    )
    if condition:
        attributes["condition"] = condition

    price = _price_to_merchant_api(data.get("price"))
    if price:
        attributes["price"] = price

    pickup_method = _normalise_enum(
        data.get("pickupMethod"),
        {
            "buy": "BUY",
            "reserve": "RESERVE",
            "ship to store": "SHIP_TO_STORE",
            "ship_to_store": "SHIP_TO_STORE",
            "not supported": "NOT_SUPPORTED",
            "not_supported": "NOT_SUPPORTED",
        },
    )
    pickup_sla = _normalise_enum(
        data.get("pickupSla"),
        {
            "same day": "SAME_DAY",
            "same_day": "SAME_DAY",
            "next day": "NEXT_DAY",
            "next_day": "NEXT_DAY",
            "two day": "TWO_DAY",
            "two_day": "TWO_DAY",
        },
    )
    if pickup_method:
        attributes["pickupMethod"] = pickup_method
    if pickup_sla:
        attributes["pickupSla"] = pickup_sla

    return {
        "offerId": offer_id,
        "contentLanguage": content_language,
        "feedLabel": feed_label,
        "productAttributes": attributes,
    }


class MerchantApiClient:
    """Small REST client for the Merchant API Products sub-API."""

    def __init__(self, credentials, merchant_id=MERCHANT_ID, session=None):
        self.merchant_id = str(merchant_id)
        self.account_name = f"accounts/{self.merchant_id}"
        self.data_source_name = _configured_data_source_name(self.merchant_id)
        self.session = session or AuthorizedSession(credentials)

    def _url(self, path):
        return f"{MERCHANT_API_BASE_URL}{path}"

    def _request(self, method, path, *, params=None, json=None):
        response = self.session.request(
            method,
            self._url(path),
            params=params,
            json=json,
            timeout=30,
        )
        if response.status_code == 404:
            raise MerchantApiNotFound(response.status_code, _normalise_api_error(response))
        if response.status_code >= 400:
            raise MerchantApiError(response.status_code, _normalise_api_error(response))
        if not response.content:
            return {}
        return response.json()

    @staticmethod
    def _product_key(offer_id, content_language="fi", feed_label="FI"):
        raw_identifier = f"{content_language.lower()}~{feed_label.upper()}~{offer_id}"
        return base64.urlsafe_b64encode(raw_identifier.encode("utf-8")).decode("ascii").rstrip("=")

    def product_name(self, offer_id, content_language="fi", feed_label="FI"):
        return (
            f"{self.account_name}/products/"
            f"{self._product_key(offer_id, content_language, feed_label)}"
        )

    def product_input_name(self, offer_id, content_language="fi", feed_label="FI"):
        return (
            f"{self.account_name}/productInputs/"
            f"{self._product_key(offer_id, content_language, feed_label)}"
        )

    def list_products(self):
        products = []
        page_token = None
        while True:
            params = {"pageSize": 1000}
            if page_token:
                params["pageToken"] = page_token
            response = self._request(
                "GET",
                f"/products/{PRODUCTS_API_VERSION}/{self.account_name}/products",
                params=params,
            )
            products.extend(response.get("products", []))
            page_token = response.get("nextPageToken")
            if not page_token:
                return products

    def get_product(self, offer_id, content_language="fi", feed_label="FI"):
        name = self.product_name(offer_id, content_language, feed_label)
        return self._request(
            "GET", f"/products/{PRODUCTS_API_VERSION}/{name}"
        )

    def upsert_product(self, product_data):
        product_input = build_merchant_product_input(product_data)
        return self._request(
            "POST",
            f"/products/{PRODUCTS_API_VERSION}/{self.account_name}/productInputs:insert",
            params={"dataSource": self.data_source_name},
            json=product_input,
        )

    def delete_product_input(self, offer_id, content_language="fi", feed_label="FI"):
        name = self.product_input_name(offer_id, content_language, feed_label)
        return self._request(
            "DELETE",
            f"/products/{PRODUCTS_API_VERSION}/{name}",
            params={"dataSource": self.data_source_name},
        )


def get_service():
    """Create a Merchant API client using the configured service account."""
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        raise FileNotFoundError(
            f"Service account file '{SERVICE_ACCOUNT_FILE}' not found."
        )
    credentials = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    return MerchantApiClient(credentials)


def is_product_managed_by_service(product, service):
    """Return whether the product is owned by this integration's data source."""
    return product.get("dataSource") == service.data_source_name


def product_exists(service, offer_id):
    """Check a processed product without treating an absent SKU as an error."""
    try:
        service.get_product(offer_id)
        return True
    except MerchantApiNotFound:
        return False


def add_product(product_data):
    """Insert a product input into the configured Merchant API data source."""
    service = get_service()
    response = service.upsert_product(product_data)
    logger.info("Merchant API product input inserted: %s", product_data["offerId"])
    return response


def update_product(product_data):
    """Refresh a product input in the configured Merchant API data source.

    ``productInputs.insert`` replaces an input with the same offer, language and
    data source, so it is the safe full-refresh operation for this catalogue.
    """
    return add_product(product_data)


def delete_product_by_offer_id(offer_id):
    """Delete only this integration's input; never delete UI-owned products."""
    service = get_service()
    try:
        service.delete_product_input(offer_id)
    except MerchantApiNotFound:
        logger.info("Merchant product input %s was already absent.", offer_id)
        return False
    logger.info("Merchant API product input deleted: %s", offer_id)
    return True


def delete_product_by_merchant_center_id(merchant_center_product_id):
    """Delete the configured-source input for a Merchant offer ID."""
    deleted = delete_product_by_offer_id(merchant_center_product_id)
    if deleted:
        return {
            "status": "success",
            "message": f"Tuote {merchant_center_product_id} poistettu Merchant API -lähteestä.",
            "deleted_product_id": merchant_center_product_id,
        }
    return {
        "status": "error",
        "message": f"Tuotetta {merchant_center_product_id} ei löytynyt tästä tietolähteestä.",
        "deleted_product_id": merchant_center_product_id,
    }


def list_all_products(service=None):
    """List processed products across all sources in the Merchant account."""
    service = service or get_service()
    return service.list_products()


def delete_all_products():
    """Delete only products owned by the configured API source.

    Merchant Center also has manually maintained products.  The old function
    could remove those 23 UI-owned items, so this deliberately scopes deletion
    to the integration's own data source.
    """
    service = get_service()
    try:
        managed_products = [
            product
            for product in list_all_products(service)
            if is_product_managed_by_service(product, service)
        ]
        deleted_count = 0
        for product in managed_products:
            if delete_product_by_offer_id(product.get("offerId", "")):
                deleted_count += 1
        return {
            "status": "success",
            "message": f"Poistettu {deleted_count} tämän API-lähteen tuotetta.",
            "deleted_count": deleted_count,
        }
    except Exception as error:
        logger.exception("Merchant API source cleanup failed")
        return {"status": "error", "message": str(error), "deleted_count": 0}


def sync_missing_products():
    """Remove unavailable products from this API source only.

    Products maintained directly in Merchant Center are intentionally left
    untouched.  This prevents an automated catalogue run from deleting them.
    """
    try:
        service = get_service()
        google_products = list_all_products(service)
        managed_offer_ids = {
            product.get("offerId")
            for product in google_products
            if product.get("offerId") and is_product_managed_by_service(product, service)
        }

        website_offer_ids = set(
            Variant.objects.filter(
                active=True,
                product__available=True,
                product__category__in=Category.objects.filter(active=True),
            )
            .exclude(item_code__isnull=True)
            .exclude(item_code="")
            .values_list("item_code", flat=True)
        )

        products_to_remove = managed_offer_ids - website_offer_ids
        removed_count = 0
        error_count = 0
        for offer_id in products_to_remove:
            try:
                if delete_product_by_offer_id(offer_id):
                    removed_count += 1
                else:
                    error_count += 1
            except Exception:
                logger.exception("Failed to remove Merchant offer %s", offer_id)
                error_count += 1

        return {
            "status": "success",
            "message": f"Synkronointi valmis. Poistettu {removed_count} tuotetta, {error_count} virhettä.",
            "removed_count": removed_count,
            "error_count": error_count,
            "products_to_remove_count": len(products_to_remove),
            "products_to_add_count": len(website_offer_ids - managed_offer_ids),
            "total_google_products": len(managed_offer_ids),
            "total_website_products": len(website_offer_ids),
        }
    except Exception as error:
        logger.exception("Merchant API product synchronization failed")
        return {
            "status": "error",
            "message": f"Synkronoinnissa tapahtui virhe: {error}",
            "removed_count": 0,
            "error_count": 1,
        }
