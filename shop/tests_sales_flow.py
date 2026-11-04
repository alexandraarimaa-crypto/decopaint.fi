from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, TestCase, SimpleTestCase

from shop.models import Product, Variant
from shop.sales_flow import (
    prepare_catalogue, product_calculator, queue_successful_add,
    consume_cart_event, backorder_dispatch_date,
)


class CatalogueAvailabilityTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.mixed = Product.objects.create(name="Synthetic mixed", slug="synthetic-mixed", price=10)
        cls.order = Product.objects.create(name="Synthetic order", slug="synthetic-order", price=10)
        cls.inactive = Product.objects.create(name="Synthetic inactive", slug="synthetic-inactive", price=10)
        for product, order, active in [(cls.mixed, False, True), (cls.mixed, False, True), (cls.mixed, True, True), (cls.order, True, True), (cls.inactive, False, False)]:
            Variant.objects.create(product=product, price=10, order_item=order, active=active, customs_code=0, weight=None)

    def test_filters_use_real_active_variants_without_duplicates(self):
        factory = RequestFactory()
        stock, context = prepare_catalogue(factory.get("/catalog/", {"availability": "stock"}), Product.objects.all())
        self.assertEqual(list(stock.values_list("pk", flat=True)), [self.mixed.pk])
        self.assertEqual(context["seo_robots"], "noindex,follow")
        order, _ = prepare_catalogue(factory.get("/catalog/", {"availability": "order"}), Product.objects.all())
        self.assertEqual(set(order.values_list("pk", flat=True)), {self.mixed.pk, self.order.pk})
        all_products, context = prepare_catalogue(factory.get("/catalog/", {"availability": "invalid"}), Product.objects.all())
        self.assertEqual(all_products.count(), 3)
        self.assertNotIn("seo_robots", context)


class SalesFlowHelpersTests(SimpleTestCase):
    def test_stock_delivery_qualifier_preserves_rich_text_entities(self):
        from shop.templatetags.sales_flow_tags import qualify_stock_delivery
        for dash in ["–", "-", "&#8211;", "&ndash;"]:
            html = f"<p>Nopea toimitus 1{dash}3 arkipäivässä • Asiantuntija-apu</p>"
            self.assertEqual(qualify_stock_delivery(html), html.replace("Nopea toimitus", "Varastotuotteiden toimitus"))

    def test_marmorino_data_correction_is_descriptive_and_guarded(self):
        from scripts.correct_marmorino_coverage import corrected
        before = {
            "attribute": {"sufficiency": "0,5-0,75kg/m2", "sufficiency_fi": "0,5-0,75kg/m2", "sufficiency_sv": "0,5-0,75 kg/m2", "sufficiency_en": "0.5-0.75kg/m2"},
            "packages": [{"id": 40, "size": "5 kg", "coverage_m2": "10-15", "price_per_m2": "4.93"}, {"id": 41, "size": "20 kg", "coverage_m2": "40-60", "price_per_m2": "4.46"}],
            "variant_fingerprint": "unchanged",
        }
        result = corrected(before)
        self.assertEqual(result["variant_fingerprint"], "unchanged")
        self.assertEqual(result["packages"][0]["coverage_m2"], "3,3–5")
        self.assertEqual(result["packages"][1]["price_per_m2"], "8.93")
        self.assertEqual(before["packages"][0]["coverage_m2"], "10-15")
        before["packages"][0]["coverage_m2"] = "owner later edit"
        with self.assertRaises(ValueError):
            corrected(before)

    def test_calculator_refuses_ambiguous_coat_rates(self):
        attributes = SimpleNamespace(first=lambda: SimpleNamespace(sufficiency="0.5–0.75 kg/m2"))
        variants = SimpleNamespace(filter=lambda **kw: SimpleNamespace(values_list=lambda *a, **kw: ["5 kg", "20 kg"]))
        product = SimpleNamespace(attributes=attributes, variants=variants)
        self.assertIsNone(product_calculator(product))
        attributes.first = lambda: SimpleNamespace(sufficiency="1–1,5 kg/m² / 2 kerrosta")
        result = product_calculator(product)
        self.assertEqual(result["calculation_rate"], 1.5)
        self.assertEqual(result["packages"][1]["amount"], 20)

    def test_success_event_uses_actual_unit_price_and_is_consumed_once(self):
        request = RequestFactory().get("/product/")
        request.session = {}
        request.user = AnonymousUser()
        product = SimpleNamespace(id=999, sku="SYNTHETIC", name="Test paint")
        variant = SimpleNamespace(pk=1, product_id=999, product=product, size="5 kg")
        cart = SimpleNamespace(cart={"999_1": {"price": "49.32"}})
        queue_successful_add(request, cart, variant, 3)
        event = consume_cart_event(request)
        self.assertEqual(event["params"]["value"], 147.96)
        self.assertEqual(event["params"]["items"][0]["price"], 49.32)
        self.assertIsNone(consume_cart_event(request))
        queue_successful_add(request, SimpleNamespace(cart={}), variant, 3)
        self.assertIsNone(consume_cart_event(request))

    def test_dispatch_estimate_uses_shop_calendar(self):
        with patch("shop.sales_flow.timezone.localdate", return_value=date(2026, 11, 4)):
            self.assertEqual(backorder_dispatch_date(), date(2026, 12, 2))
