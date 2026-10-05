from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock, call, patch

from django.test import SimpleTestCase, TestCase, override_settings

from google_shopping.tasks import (
    build_existing_merchant_update_plan,
    build_product_data_from_variant,
    get_storefront_variant_for_product,
    incremental_update_optimized_single_variant,
    normalize_product_data_for_merchant_api,
    process_existing_merchant_batch,
    public_regular_price,
    sync_order_products,
)
from google_shopping.api import build_merchant_product_input
from shop.models import Product, Variant


class MerchantPayloadTests(SimpleTestCase):
    def test_legacy_pickup_fields_are_normalized(self):
        payload = normalize_product_data_for_merchant_api({
            "offerId": "TEST-1",
            "pickup_method": "buy",
            "pickup_SLA": "same_day",
            "storeCode": "decopaint_kaarina",
        })

        self.assertEqual(payload["pickupMethod"], "buy")
        self.assertEqual(payload["pickupSla"], "same_day")
        self.assertNotIn("pickup_method", payload)
        self.assertNotIn("pickup_SLA", payload)
        self.assertNotIn("storeCode", payload)

    def test_legacy_product_payload_is_translated_for_merchant_api(self):
        product_input = build_merchant_product_input({
            "offerId": "TEST-1",
            "contentLanguage": "fi",
            "targetCountry": "FI",
            "title": "Test product",
            "description": "Test description",
            "link": "https://decopaint.fi/test-product/",
            "imageLink": "https://decopaint.fi/test.jpg",
            "availability": "in stock",
            "condition": "new",
            "price": {"value": "12.34", "currency": "EUR"},
            "pickupMethod": "buy",
            "pickupSla": "same_day",
        })

        self.assertEqual(product_input["feedLabel"], "FI")
        self.assertNotIn("targetCountry", product_input)
        self.assertEqual(
            product_input["productAttributes"]["price"],
            {"amountMicros": "12340000", "currencyCode": "EUR"},
        )
        self.assertEqual(
            product_input["productAttributes"]["availability"], "IN_STOCK"
        )
        self.assertEqual(product_input["productAttributes"]["condition"], "NEW")
        self.assertEqual(product_input["productAttributes"]["pickupMethod"], "BUY")
        self.assertEqual(product_input["productAttributes"]["pickupSla"], "SAME_DAY")

    @patch("google_shopping.tasks.ProductImage.objects.filter")
    def test_builder_emits_content_api_pickup_fields(self, filter_mock):
        filtered = filter_mock.return_value
        first_excluded = filtered.exclude.return_value
        second_excluded = first_excluded.exclude.return_value
        second_excluded.order_by.return_value = []

        product = SimpleNamespace(
            id=10,
            image=None,
            thumbnail=None,
            name="Test product",
            description="Test description",
            category=SimpleNamespace(all=lambda: []),
            attributes=SimpleNamespace(first=lambda: None),
            get_absolute_url=lambda: "/product/test-product/",
        )
        variant = SimpleNamespace(
            id=20,
            product=product,
            product_id=product.id,
            item_code="TEST-1",
            order_item=False,
            total_price=lambda: Decimal("12.34"),
        )

        variant.price = Decimal("12.34")
        product.multiplier = Decimal("1")
        variant.get_group_settings = lambda user=None: SimpleNamespace(
            tax=SimpleNamespace(rate=Decimal("0")),
            multiplier=SimpleNamespace(multi=Decimal("1")),
        )

        payload = build_product_data_from_variant(
            variant,
            storefront_variant=variant,
        )

        self.assertEqual(payload["pickupMethod"], "buy")
        self.assertEqual(payload["pickupSla"], "same_day")
        self.assertNotIn("pickup_method", payload)
        self.assertNotIn("pickup_SLA", payload)
        self.assertNotIn("storeCode", payload)

    @patch("google_shopping.tasks.ProductImage.objects.filter")
    def test_builder_omits_pickup_for_out_of_stock_product(self, filter_mock):
        filtered = filter_mock.return_value
        first_excluded = filtered.exclude.return_value
        second_excluded = first_excluded.exclude.return_value
        second_excluded.order_by.return_value = []

        product = SimpleNamespace(
            id=11,
            image=None,
            thumbnail=None,
            name="Order product",
            description="Test description",
            category=SimpleNamespace(all=lambda: []),
            attributes=SimpleNamespace(first=lambda: None),
            get_absolute_url=lambda: "/product/order-product/",
        )
        variant = SimpleNamespace(
            id=21,
            product=product,
            product_id=product.id,
            item_code="TEST-2",
            order_item=True,
            total_price=lambda: Decimal("9.99"),
        )

        variant.price = Decimal("9.99")
        product.multiplier = Decimal("1")
        variant.get_group_settings = lambda user=None: SimpleNamespace(
            tax=SimpleNamespace(rate=Decimal("0")),
            multiplier=SimpleNamespace(multi=Decimal("1")),
        )

        payload = build_product_data_from_variant(
            variant,
            storefront_variant=variant,
        )

        self.assertEqual(payload["availability"], "out of stock")
        self.assertNotIn("pickupMethod", payload)
        self.assertNotIn("pickupSla", payload)

    @patch("google_shopping.tasks.ProductImage.objects.filter")
    def test_builder_uses_storefront_regular_price_with_stable_offer_id(
        self,
        filter_mock,
    ):
        filtered = filter_mock.return_value
        filtered.exclude.return_value.exclude.return_value.order_by.return_value = []

        product = SimpleNamespace(
            id=1435,
            multiplier=Decimal("1"),
            image=None,
            thumbnail=None,
            name="305 BioLavabile",
            description="Test description",
            category=SimpleNamespace(all=lambda: []),
            attributes=SimpleNamespace(first=lambda: None),
            get_absolute_url=lambda: "/product/305-biolavabile/",
        )
        merchant_offer = SimpleNamespace(
            id=47002,
            product=product,
            product_id=product.id,
            item_code="W03050TR0E",
            order_item=False,
        )
        storefront_variant = SimpleNamespace(
            id=47005,
            product=product,
            product_id=product.id,
            item_code="W03050000E",
            price=Decimal("14.25"),
            order_item=False,
            get_group_settings=lambda user=None: SimpleNamespace(
                tax=SimpleNamespace(rate=Decimal("25.5")),
                multiplier=SimpleNamespace(multi=Decimal("1.5")),
            ),
        )

        payload = build_product_data_from_variant(
            merchant_offer,
            storefront_variant=storefront_variant,
        )

        self.assertEqual(payload["offerId"], "W03050TR0E")
        self.assertEqual(payload["price"], {"value": "26.83", "currency": "EUR"})
        self.assertEqual(payload["link"], "https://decopaint.fi/product/305-biolavabile/")

    def test_public_regular_price_does_not_apply_product_discount(self):
        product = SimpleNamespace(multiplier=Decimal("1"), discount_percentage=20)
        variant = SimpleNamespace(
            id=47005,
            product=product,
            price=Decimal("14.25"),
            get_group_settings=lambda user=None: SimpleNamespace(
                tax=SimpleNamespace(rate=Decimal("25.5")),
                multiplier=SimpleNamespace(multi=Decimal("1.5")),
            ),
        )

        self.assertEqual(public_regular_price(variant), Decimal("26.83"))


class StorefrontVariantSelectionTests(TestCase):
    def test_prefers_visible_white_variant_over_hidden_base_variant(self):
        product = Product.objects.create(
            name="305 BioLavabile",
            slug="305-biolavabile",
            price=Decimal("13.00"),
        )
        Variant.objects.create(
            product=product,
            item_code="W03050TR0E",
            item_description="BIANCO 305 BASE TR LT. 1",
            size="1 L",
            color2="Valkoinen",
            base="base",
            price=Decimal("13.00"),
            customs_code=None,
            weight=None,
        )
        storefront_variant = Variant.objects.create(
            product=product,
            item_code="W03050000E",
            item_description="BIANCO 305 LT. 1",
            size="1 L",
            color2="Valkoinen",
            price=Decimal("14.25"),
            customs_code=None,
            weight=None,
        )
        Variant.objects.create(
            product=product,
            item_code="W03050000D",
            item_description="BIANCO 305 LT. 4",
            size="4 L",
            color2="Valkoinen",
            price=Decimal("45.70"),
            customs_code=None,
            weight=None,
        )

        selected = get_storefront_variant_for_product(product.id)

        self.assertEqual(selected.id, storefront_variant.id)
        self.assertEqual(selected.item_code, "W03050000E")


class ExistingOnlyMerchantSyncTests(TestCase):
    def test_plan_matches_legacy_offer_by_landing_page(self):
        product = Product.objects.create(
            name="305 BioLavabile",
            slug="305-biolavabile",
            price=Decimal("13.00"),
            available=True,
        )
        service = SimpleNamespace(data_source_name="accounts/1/dataSources/2")
        uploaded_products = [
            {
                "offerId": "LEGACY-305",
                "dataSource": service.data_source_name,
                "productAttributes": {
                    "link": "https://decopaint.fi/product/305-biolavabile/?source=google",
                },
            },
            {
                "offerId": "OTHER-SOURCE",
                "dataSource": "accounts/1/dataSources/999",
                "productAttributes": {
                    "link": "https://decopaint.fi/product/305-biolavabile/",
                },
            },
        ]

        plan = build_existing_merchant_update_plan(uploaded_products, service)

        self.assertEqual(
            plan,
            [{"offer_id": "LEGACY-305", "product_id": product.id}],
        )

    @override_settings(MERCHANT_SYNC_ENABLED=True)
    @patch("google_shopping.tasks.time.sleep")
    @patch("google_shopping.tasks.async_task")
    @patch("google_shopping.tasks.build_existing_merchant_update_plan")
    @patch("google_shopping.tasks.list_all_products")
    @patch("google_shopping.tasks.get_service")
    def test_nightly_sync_schedules_existing_offers_only(
        self,
        service_mock,
        list_products_mock,
        plan_mock,
        async_task_mock,
        sleep_mock,
    ):
        service = service_mock.return_value
        list_products_mock.return_value = [{"offerId": "EXISTING-1"}]
        plan_mock.return_value = [
            {"offer_id": "EXISTING-1", "product_id": 101},
        ]

        result = incremental_update_optimized_single_variant(product_batch_size=20)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["products_to_update"], 1)
        self.assertEqual(result["added_count"], 0)
        self.assertEqual(result["removed_count"], 0)
        plan_mock.assert_called_once_with(list_products_mock.return_value, service)
        async_task_mock.assert_called_once_with(
            "google_shopping.tasks.process_existing_merchant_batch",
            [{"offer_id": "EXISTING-1", "product_id": 101}],
            "https://decopaint.fi",
            hook="google_shopping.tasks.single_variant_batch_complete_hook",
            group="google_shopping_existing_batch_0",
        )
        sleep_mock.assert_called_once_with(0.2)

    @override_settings(MERCHANT_SYNC_ENABLED=True)
    @patch("google_shopping.tasks.time.sleep")
    @patch("google_shopping.tasks.delete_product_by_offer_id")
    @patch("google_shopping.tasks.add_product")
    @patch("google_shopping.tasks.update_product")
    @patch("google_shopping.tasks.build_product_data_from_variant")
    @patch("google_shopping.tasks.get_storefront_variant_for_product")
    @patch("google_shopping.tasks.list_all_products")
    @patch("google_shopping.tasks.get_service")
    def test_batch_updates_existing_offer_without_add_or_delete(
        self,
        service_mock,
        list_products_mock,
        storefront_variant_mock,
        build_payload_mock,
        update_product_mock,
        add_product_mock,
        delete_product_mock,
        sleep_mock,
    ):
        service = service_mock.return_value
        service.data_source_name = "accounts/1/dataSources/2"
        list_products_mock.return_value = [
            {
                "offerId": "W03050TR0E",
                "dataSource": service.data_source_name,
            },
        ]
        storefront_variant = storefront_variant_mock.return_value
        build_payload_mock.return_value = {
            "offerId": "W03050TR0E",
            "price": {"value": "26.83", "currency": "EUR"},
        }

        result = process_existing_merchant_batch(
            [{"offer_id": "W03050TR0E", "product_id": 1435}]
        )

        self.assertEqual(result["updated"], 1)
        self.assertEqual(result["added"], 0)
        self.assertEqual(result["removed"], 0)
        build_payload_mock.assert_called_once_with(
            storefront_variant,
            "https://decopaint.fi",
            storefront_variant=storefront_variant,
            offer_id="W03050TR0E",
        )
        update_product_mock.assert_called_once_with(build_payload_mock.return_value)
        add_product_mock.assert_not_called()
        delete_product_mock.assert_not_called()
        sleep_mock.assert_called_once_with(1)

    @override_settings(MERCHANT_SYNC_ENABLED=False)
    @patch("google_shopping.tasks.get_service")
    def test_nightly_sync_respects_kill_switch(self, service_mock):
        result = incremental_update_optimized_single_variant()

        self.assertEqual(result["status"], "disabled")
        service_mock.assert_not_called()


class OrderTriggeredMerchantSyncTests(SimpleTestCase):
    @override_settings(MERCHANT_SYNC_ENABLED=True)
    @patch("google_shopping.tasks.process_single_product_update")
    @patch("order.models.OrderItem.objects")
    def test_syncs_distinct_order_products_without_deletion(
        self,
        order_items_mock,
        process_mock,
    ):
        values = (
            order_items_mock
            .filter.return_value
            .exclude.return_value
            .values_list.return_value
        )
        values.distinct.return_value = [101, 202]
        process_mock.side_effect = [
            {"status": "updated"},
            {"status": "added"},
        ]

        result = sync_order_products(55)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["product_count"], 2)
        self.assertEqual(
            process_mock.call_args_list,
            [
                call(
                    101,
                    "https://decopaint.fi",
                    delete_if_unavailable=False,
                ),
                call(
                    202,
                    "https://decopaint.fi",
                    delete_if_unavailable=False,
                ),
            ],
        )
