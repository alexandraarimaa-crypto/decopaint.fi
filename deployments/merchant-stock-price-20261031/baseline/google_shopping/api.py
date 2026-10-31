"""Google Merchant API v1 adapter for the DecoPaint product synchronisation."""

import logging
import os
from urllib.parse import quote

from django.conf import settings
from google.auth.transport.requests import AuthorizedSession
from google.oauth2.service_account import Credentials
from shop.models import Category, Variant

from .merchant_payload import legacy_to_product_input, product_input_id


logger = logging.getLogger(__name__)

SERVICE_ACCOUNT_FILE = os.path.join(os.path.dirname(__file__), "client_secret.json")
SCOPES = ["https://www.googleapis.com/auth/content"]
MERCHANT_ID = "5351296674"
API_ROOT = "https://merchantapi.googleapis.com"
QUOTA_PROJECT_ID = "smiling-pact-399412"


class MerchantApiError(RuntimeError):
    """Sanitised Merchant API error that never includes access credentials."""


class MerchantApiService:
    def __init__(self, session, data_source_name):
        self.session = session
        self.data_source_name = data_source_name
        self.merchant_id = MERCHANT_ID

    def request(self, method, path, *, params=None, json=None, allow_not_found=False):
        response = self.session.request(
            method,
            f"{API_ROOT}{path}",
            params=params,
            json=json,
            timeout=45,
        )
        if allow_not_found and response.status_code == 404:
            return None
        if not response.ok:
            message = ""
            try:
                error = response.json().get("error", {})
                message = error.get("message", "")
            except Exception:
                pass
            raise MerchantApiError(
                f"Merchant API HTTP {response.status_code}: {message[:500]}"
            )
        return response.json() if response.content else {}


def _configured_data_source_name():
    default = f"accounts/{MERCHANT_ID}/dataSources/10433825709"
    value = getattr(settings, "MERCHANT_API_DATA_SOURCE", "") or os.environ.get(
        "MERCHANT_API_DATA_SOURCE", default
    )
    expected_prefix = f"accounts/{MERCHANT_ID}/dataSources/"
    if not str(value).startswith(expected_prefix):
        raise RuntimeError("MERCHANT_API_DATA_SOURCE has an invalid account")
    return str(value)


def get_service():
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        raise FileNotFoundError(f"Service account file '{SERVICE_ACCOUNT_FILE}' not found")
    credentials = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    ).with_quota_project(QUOTA_PROJECT_ID)
    return MerchantApiService(
        AuthorizedSession(credentials),
        _configured_data_source_name(),
    )


def _product_path(offer_id, content_language="fi", feed_label="FI", resource="products"):
    product_id = product_input_id(offer_id, content_language, feed_label)
    encoded = quote(product_id, safe="~")
    return f"/products/v1/accounts/{MERCHANT_ID}/{resource}/{encoded}"


def product_exists(service, offer_id):
    response = service.request(
        "GET", _product_path(offer_id), allow_not_found=True
    )
    return response is not None


def _upsert_product(product_data):
    service = get_service()
    body = legacy_to_product_input(product_data)
    response = service.request(
        "POST",
        f"/products/v1/accounts/{MERCHANT_ID}/productInputs:insert",
        params={"dataSource": service.data_source_name},
        json=body,
    )
    logger.info("Merchant API upsert completed for %s", body["offerId"])
    return response


def add_product(product_data):
    return _upsert_product(product_data)


def update_product(product_data):
    return _upsert_product(product_data)


def delete_product_by_offer_id(offer_id):
    service = get_service()
    response = service.request(
        "DELETE",
        _product_path(offer_id, resource="productInputs"),
        params={"dataSource": service.data_source_name},
        allow_not_found=True,
    )
    if response is None:
        logger.info("Product input %s is not owned by this source", offer_id)
        return False
    logger.info("Product input %s deleted", offer_id)
    return True


def delete_product_by_merchant_center_id(merchant_center_product_id):
    deleted = delete_product_by_offer_id(merchant_center_product_id)
    if deleted:
        return {
            "status": "success",
            "message": f"Tuote {merchant_center_product_id} poistettu onnistuneesti Google Merchant Centeristä.",
            "deleted_product_id": merchant_center_product_id,
        }
    return {
        "status": "error",
        "message": f"Tuotetta {merchant_center_product_id} ei löytynyt tästä tietolähteestä.",
        "deleted_product_id": merchant_center_product_id,
    }


def list_all_products(service=None):
    service = service or get_service()
    products = []
    page_token = None
    while True:
        params = {"pageSize": 1000}
        if page_token:
            params["pageToken"] = page_token
        response = service.request(
            "GET",
            f"/products/v1/accounts/{MERCHANT_ID}/products",
            params=params,
        )
        products.extend(response.get("products", []))
        page_token = response.get("nextPageToken")
        if not page_token:
            break
    return products


def is_product_managed_by_service(product, service):
    return bool(product) and product.get("dataSource") == service.data_source_name


def delete_all_products():
    """Intentionally disabled: bulk deletion is unsafe in a multi-source account."""
    logger.error("Bulk Merchant product deletion was blocked by the safety guard")
    return {
        "status": "error",
        "message": "Massapoisto on poistettu käytöstä turvallisuussyistä.",
        "deleted_count": 0,
    }


def sync_missing_products():
    """Delete only stale product inputs that are owned by this API source."""
    try:
        service = get_service()
        products = list_all_products(service)
        managed_offer_ids = {
            product.get("offerId")
            for product in products
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
        removed_count = sum(
            1 for offer_id in products_to_remove if delete_product_by_offer_id(offer_id)
        )
        return {
            "status": "success",
            "message": f"Synkronointi valmis. Poistettu {removed_count} tuotetta.",
            "removed_count": removed_count,
            "error_count": 0,
            "products_to_remove_count": len(products_to_remove),
            "products_to_add_count": len(website_offer_ids - managed_offer_ids),
            "total_google_products": len(managed_offer_ids),
            "total_website_products": len(website_offer_ids),
        }
    except Exception as exc:
        logger.error("Merchant product synchronisation failed: %s", exc)
        return {
            "status": "error",
            "message": f"Synkronoinnissa tapahtui virhe: {exc}",
            "removed_count": 0,
            "error_count": 1,
        }
