"""Small storefront helpers; never change order, stock or price calculations."""
from datetime import timedelta

from django.db.models import Exists, OuterRef
from django.utils import timezone

from .models import Variant


def prepare_catalogue(request, products):
    variants = Variant.objects.filter(product_id=OuterRef("pk"), active=True)
    products = products.annotate(
        sales_in_stock=Exists(variants.filter(order_item=False)),
        sales_on_order=Exists(variants.filter(order_item=True)),
    )
    availability = request.GET.get("availability", "")
    if availability == "stock":
        products = products.filter(sales_in_stock=True)
    elif availability == "order":
        products = products.filter(sales_on_order=True)
    else:
        availability = ""
    return products, {
        "sales_availability": availability,
        "sales_page_prefix": "availability=" + availability + "&" if availability else "",
        **({"seo_robots": "noindex,follow"} if availability else {}),
    }


def backorder_dispatch_date():
    return timezone.localdate() + timedelta(days=28)


def queue_successful_add(request, cart, variant, quantity):
    """Only call after Cart.add succeeds. No browser submit approximation."""
    from .analytics import _item, _money

    key = f"{variant.product_id}_{variant.pk}"
    stored = cart.cart.get(key)
    if not stored:
        return
    item = _item(variant.product, variant=variant, price=stored["price"], quantity=quantity)
    request.session["sales_cart_event"] = {
        "name": "add_to_cart",
        "params": {"currency": "EUR", "value": _money(item["price"] * item["quantity"]), "items": [item]},
    }


def consume_cart_event(request):
    # Do not consume the redirect event while a concurrent price AJAX request runs.
    if request.method != "GET" or request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return None
    return request.session.pop("sales_cart_event", None)
