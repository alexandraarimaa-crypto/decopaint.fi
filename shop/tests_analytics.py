import json
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, override_settings

from shop.analytics import (
    analytics_user_id,
    build_google_ads_enhanced_conversion_data,
    build_google_customer_reviews_data,
    build_purchase_event,
    build_search_event,
)


class AnalyticsPayloadTests(SimpleTestCase):
    def test_customer_reviews_widget_uses_order_page_language(self):
        template = (
            Path(__file__).resolve().parent.parent
            / "order"
            / "templates"
            / "order"
            / "created.html"
        ).read_text(encoding="utf-8")

        self.assertIn("{% get_current_language as google_customer_reviews_language %}", template)
        self.assertIn("window.___gcfg.lang", template)
        self.assertIn("google_customer_reviews_language|default:'fi'|escapejs", template)

    @override_settings(
        SECRET_KEY="test-secret",
        ANALYTICS_USER_ID_SALT="analytics-test-salt",
    )
    def test_user_id_is_stable_and_contains_no_profile_data(self):
        user = SimpleNamespace(
            pk=42,
            is_authenticated=True,
            email="customer@example.test",
        )

        first = analytics_user_id(user)
        second = analytics_user_id(user)

        self.assertEqual(first, second)
        self.assertTrue(first.startswith("dp_"))
        self.assertNotIn("customer", first)
        self.assertNotIn("@", first)

    def test_search_event_redacts_contact_data(self):
        event = build_search_event(
            "customer@example.test +358 40 123 4567 kalkkimaali",
            3,
        )

        serialized = json.dumps(event)
        self.assertNotIn("customer@example.test", serialized)
        self.assertNotIn("358 40 123 4567", serialized)
        self.assertEqual(event["params"]["result_count"], 3)

    @patch("order.models.Order.objects")
    def test_purchase_uses_order_values_and_never_customer_pii(self, orders_mock):
        orders_mock.filter.return_value.exclude.return_value.exists.return_value = True
        category = SimpleNamespace(name="Sisustusmaalit")
        product = SimpleNamespace(
            id=7,
            sku="PRODUCT-7",
            name="Marmora Romana",
            category=SimpleNamespace(first=lambda: category),
        )
        variant = SimpleNamespace(
            item_code="FM0000000W",
            product=product,
            size="5 kg",
            color="Valkoinen",
            grain="",
            gloss="",
            base="",
        )
        order_item = SimpleNamespace(
            variant=variant,
            quantity=2,
            price="120.00",
        )
        item_query = MagicMock()
        item_query.select_related.return_value.all.return_value = [order_item]
        order = SimpleNamespace(
            pk=99,
            user_id=5,
            email="customer@example.test",
            first_name="Test",
            last_name="Customer",
            phone="+358401234567",
            address="Testikatu 1",
            notes="Leave at the door",
            payment_method="online",
            shipping_method="postnord_lokero",
            coupon=SimpleNamespace(code="KESÄ10"),
            items=item_query,
            get_total_price=lambda: "130.00",
            get_total_tax=lambda: "26.41",
            get_delivery_price=lambda: "10.00",
        )

        event = build_purchase_event(order)
        serialized = json.dumps(event, ensure_ascii=False)

        self.assertEqual(event["name"], "purchase")
        self.assertEqual(event["params"]["transaction_id"], "DP-99")
        self.assertEqual(event["params"]["customer_type"], "returning")
        self.assertEqual(event["params"]["items"][0]["item_id"], "FM0000000W")
        self.assertEqual(event["params"]["items"][0]["price"], 60.0)
        for forbidden in [
            "customer@example.test",
            "Testikatu",
            "+358401234567",
            "Leave at the door",
        ]:
            self.assertNotIn(forbidden, serialized)

    def test_enhanced_conversion_data_is_separate_and_normalized(self):
        order = SimpleNamespace(
            email=" Customer@Example.Test ",
            phone="+358 40 123 4567",
            first_name=" Test ",
            last_name=" Customer ",
            address=" Testikatu 1 ",
            city=" Helsinki ",
            postal=" 00100 ",
        )

        payload = build_google_ads_enhanced_conversion_data(order)

        self.assertEqual(payload["email"], "customer@example.test")
        self.assertEqual(payload["phone_number"], "+358401234567")
        self.assertEqual(
            payload["address"],
            {
                "first_name": "Test",
                "last_name": "Customer",
                "street": "Testikatu 1",
                "city": "Helsinki",
                "postal_code": "00100",
                "country": "FI",
            },
        )

    def test_enhanced_conversion_omits_invalid_phone_number(self):
        order = SimpleNamespace(
            email="customer@example.test",
            phone="040 123 4567",
            first_name="Test",
            last_name="Customer",
            address="Testikatu 1",
            city="Helsinki",
            postal="00100",
        )

        payload = build_google_ads_enhanced_conversion_data(order)

        self.assertNotIn("phone_number", payload)

    @patch("shop.analytics.timezone.localdate", return_value=date(2026, 8, 7))
    def test_customer_reviews_uses_only_required_order_data(self, _localdate):
        order_item = SimpleNamespace(barcode="5901234123457", variant=None)
        item_query = MagicMock()
        item_query.select_related.return_value.all.return_value = [order_item]
        order = SimpleNamespace(
            pk=99,
            email="customer@example.test",
            shipping_method="postnord_lokero",
            items=item_query,
        )

        payload = build_google_customer_reviews_data(order)

        self.assertEqual(payload["merchant_id"], 5351296674)
        self.assertEqual(payload["order_id"], "DP-99")
        self.assertEqual(payload["email"], "customer@example.test")
        self.assertEqual(payload["delivery_country"], "FI")
        self.assertEqual(payload["estimated_delivery_date"], "2026-08-11")
        self.assertEqual(payload["products"], [{"gtin": "5901234123457"}])
