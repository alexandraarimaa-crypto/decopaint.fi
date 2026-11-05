"""Build scoped, hash-guarded changes onto the audited deployed source."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "deployments/sales-flow-20261103/baseline"
SOURCE_HASHES = json.loads((BASE.parent / "runtime-source-manifest.json").read_text())


def baseline(name):
    data = (BASE / name).read_bytes()
    if hashlib.sha256(data).hexdigest() != SOURCE_HASHES[name]:
        raise ValueError("Audited source changed: " + name)
    return data.decode("utf-8")


def replace_once(text, before, after):
    if text.count(before) != 1:
        raise ValueError("Audited anchor changed: " + before[:100])
    return text.replace(before, after, 1)


def build(output):
    out = Path(output)
    files = {}
    for name in ["shop/measurement_identity.py", "shop/static/assets/js/analytics.js",
                 "shop/static/assets/js/analytics-location.js", "shop/sales_flow.py",
                 "shop/material_calculator.py", "shop/templatetags/sales_flow_tags.py",
                 "shop/templates/shop/product/sales_calculator.html",
                 "shop/templates/shop/product/sales_catalogue.html",
                 "shop/static/assets/js/sales-product.js", "shop/static/assets/css/sales-flow.css"]:
        files[name] = (ROOT / name).read_text()

    name = "order/attribution.py"
    text = baseline(name)
    text = replace_once(text, "from django.conf import settings\n", "from django.conf import settings\nfrom shop.measurement_identity import parse_ga_client_id, parse_ga_session_id\n")
    text = replace_once(text, '"ga_client_id": _clean_ga_cookie(request.COOKIES.get("_ga", "")),', '"ga_client_id": parse_ga_client_id(request.COOKIES.get("_ga", "")),')
    text = replace_once(text, '"ga_session_id": _clean_ga_cookie(', '"ga_session_id": parse_ga_session_id(')
    files[name] = text

    name = "order/ga4.py"
    text = baseline(name)
    text = replace_once(text, "from shop.analytics import build_purchase_event\n", "from shop.analytics import build_purchase_event\nfrom shop.measurement_identity import parse_ga_client_id, parse_ga_session_id\n")
    text = replace_once(text, '    if order.ga_session_id:\n        params["session_id"] = order.ga_session_id\n', '    session_id = parse_ga_session_id(order.ga_session_id)\n    if session_id:\n        params["session_id"] = int(session_id)\n    client_id = parse_ga_client_id(order.ga_client_id)\n    if not client_id:\n        raise ValueError("A valid consented web client identity is required")\n')
    text = replace_once(text, '"client_id": order.ga_client_id,', '"client_id": client_id,')
    text = replace_once(text, '            if not order.ga_client_id:\n', '            if not parse_ga_client_id(order.ga_client_id):\n')
    files[name] = text

    name = "shop/templates/shop/base/base.html"
    text = baseline(name)
    anchor = '<script async src="https://www.googletagmanager.com/gtag/js?id={{ analytics.measurement_id|urlencode }}"></script>'
    text = replace_once(text, anchor, anchor + '\n<script src="{% static \'assets/js/analytics-location.js\' %}?v=20261103"></script>')
    text = replace_once(text, "// Never copy checkout/search query parameters into Analytics.", "// Keep only validated campaign identifiers; exclude arbitrary form/search data.")
    text = replace_once(text, "'page_location': window.location.origin + window.location.pathname", "'page_location': window.DecoPaintAnalyticsLocation(window.location.href) || (window.location.origin + window.location.pathname)")
    text = replace_once(text, '<script defer src="{% static \'assets/js/analytics.js\' %}"></script>', '<script defer src="{% static \'assets/js/analytics.js\' %}?v=20261103"></script>')
    text = replace_once(text, '<meta name="viewport"', '<link rel="stylesheet" href="{% static \'assets/css/sales-flow.css\' %}?v=20261104">\n<meta name="viewport"')
    text = replace_once(text, '{{ ga4_event|json_script:"ga4-page-event" }}', '{{ ga4_event|json_script:"ga4-page-event" }}\n{{ sales_cart_event|json_script:"ga4-cart-event" }}')
    files[name] = text

    name = "shop/context_processors.py"
    text = baseline(name)
    text = replace_once(text, "from .models import StoreSettings", "from .models import StoreSettings\nfrom .sales_flow import consume_cart_event")
    text = replace_once(text, "'store_settings': settings,", "'store_settings': settings,\n        'sales_cart_event': consume_cart_event(request),")
    files[name] = text

    name = "cart/views.py"
    text = baseline(name)
    text = replace_once(text, "from shop.analytics import build_cart_event, build_cart_params", "from shop.analytics import build_cart_event, build_cart_params\nfrom shop.sales_flow import queue_successful_add")
    text = replace_once(text, '                    messages.success(request, f"{variant.product.name} lisätty koriin.")', '''                    if not cleaned_data['update']:
                        try:
                            queue_successful_add(request, cart, variant, cleaned_data['quantity'])
                        except Exception:
                            pass  # Measurement must never interrupt a successful cart write.
                    messages.success(request, f"{variant.product.name} lisätty koriin.")''')
    files[name] = text

    name = "shop/views.py"
    text = baseline(name)
    text = "from shop.sales_flow import prepare_catalogue\n" + text
    for function, following in [("all_products", "product_list"), ("product_list", "product_list_by_tag")]:
        start = text.index("def " + function + "(")
        end = text.index("def " + following + "(", start + 4)
        section = text[start:end]
        section = replace_once(section, "    paginator = Paginator(products, products_per_page)", "    products, sales_context = prepare_catalogue(request, products)\n    paginator = Paginator(products, products_per_page)")
        section = replace_once(section, "    context = {", "    context = {\n        **sales_context,")
        text = text[:start] + section + text[end:]
    files[name] = text

    name = "shop/templates/shop/product/list.html"
    text = baseline(name)
    text = replace_once(text, '<section class="container container-xxl mt-6 dp-catalog-count">', '{% include "shop/product/sales_catalogue.html" %}\n<section class="container container-xxl mt-6 dp-catalog-count">')
    text = text.replace('href="?page=', 'href="?{{ sales_page_prefix }}page=')
    files[name] = text

    name = "shop/templates/shop/product/detail.html"
    text = baseline(name)
    start = text.index("<script>\ndocument.addEventListener('DOMContentLoaded', function() {\n    const cartForm = document.getElementById('cart_form');")
    end = text.index("</script>", start) + len("</script>")
    text = text[:start] + "<!-- add_to_cart is emitted only after a successful server cart write. -->" + text[end:]
    text = replace_once(text, '      <div class="d-flex align-items-center fs-15px mb-6">', '      <div class="d-flex align-items-center fs-15px mb-6">\n        {% if total_reviews %}')
    text = replace_once(text, '          <a href="#reviews" class="border-start', '        {% endif %}\n          <a href="#reviews" class="border-start')
    text = replace_once(text, '        <div class="quantity-price-row">', '        {% include "shop/product/sales_calculator.html" %}\n        <div class="quantity-price-row">')
    text = replace_once(text, '        function showPriceLoading() {', '        function showPriceLoading() {\n            document.dispatchEvent(new Event("decopaint:price-loading"));')
    text = replace_once(text, '                        var unit_price = parseFloat(data.price);', '''                        var unit_price = parseFloat(data.price);
                        if (!pendingPriceUpdate && Number.isFinite(unit_price) && unit_price > 0) {
                            document.dispatchEvent(new CustomEvent("decopaint:price-ready", {detail: {price: unit_price, size: size}}));
                        }''')
    before = '''                            var estimatedAvailability = new Date();
                            estimatedAvailability.setDate(estimatedAvailability.getDate() + 28);
                            var estimatedAvailabilityText = new Intl.DateTimeFormat('fi-FI', {
                                day: 'numeric',
                                month: 'numeric',
                                year: 'numeric'
                            }).format(estimatedAvailability);
                            $('#delivery-container').html(
                                'Toimitusaika on n. 2-4 viikkoa. ' +
                                'Arvioitu lähetyspäivä viimeistään ' +
                                estimatedAvailabilityText + '.'
                            );'''
    text = replace_once(text, before, "                            $('#delivery-container').text('Toimitusaika noin 2–4 viikkoa.');")
    files[name] = text

    name = "cart/templates/cart/checkout.html"
    text = baseline(name)
    # Put the note in each product's text column, never the narrow thumbnail.
    anchor = '{% if item.variant_info.id and item.variant_info.id != 0 %}'
    if text.count(anchor) != 2:
        raise ValueError("Checkout delivery anchors changed")
    note = '{% if item.variant_info.order_item %}<p class="dp-sales-delivery">Toimitusaika noin 2–4 viikkoa.</p>{% endif %}\n'
    text = text.replace(anchor, note + anchor)
    files[name] = text

    name = "shop/templates/shop/base/top_bar.html"
    text = baseline(name)
    text = replace_once(text, '{% load i18n %}', '{% load i18n sales_flow_tags %}')
    text = replace_once(text, '{{ top_bar|safe }}', '{{ top_bar|qualify_stock_delivery|safe }}')
    text = text.replace("Nopea toimitus 1–3 arkipäivässä", "Varastotuotteet 1–3 arkipäivässä")
    text = text.replace("Toimitus 1–3 pv · Maksuton palautus", "Varastotuotteet 1–3 pv · Tilaustuotteet 2–4 vk")
    files[name] = text
    name = "shop/templates/shop/base/footer.html"
    files[name] = baseline(name).replace("Nopea toimitus 1–3 arkipäivässä", "Varastotuotteet 1–3 arkipäivässä")

    for name, text in files.items():
        target = out / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    manifest = {
        "release_files": sorted(files),
        "expected_production_sha256": {name: SOURCE_HASHES.get(name) for name in files},
        "sha256": {name: hashlib.sha256((out / name).read_bytes()).hexdigest() for name in files},
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / "sales-flow-release.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    print("Built", len(build(args.output)["release_files"]), "scoped files; no database or network operation.")
