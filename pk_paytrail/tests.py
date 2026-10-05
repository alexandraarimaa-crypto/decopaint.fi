from decimal import Decimal
import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from urllib.parse import quote

from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse

from order.models import Order
from pk_paytrail.hmac_calculator import Crypto
from users.models import CustomUser


def make_order(**overrides):
    values = {
        "first_name": "Test",
        "last_name": "Customer",
        "email": "customer@example.test",
        "address": "Testikatu 1",
        "postal": "00100",
        "city": "Helsinki",
        "phone": "0400000000",
        "total_price": "10.00",
        "payment_method": "online",
        "status": "new",
        "payed": False,
        "transaction_id": "transaction-1",
    }
    values.update(overrides)
    return Order.objects.create(**values)


def signed_params(order, *, status="ok", amount=None, transaction_id=None, extra=None):
    params = {
        "checkout-account": str(settings.PK_PAYTRAIL_MERCHANT_ID),
        "checkout-algorithm": "sha256",
        "checkout-amount": str(
            amount
            if amount is not None
            else int(Decimal(str(order.total_price)) * 100)
        ),
        "checkout-stamp": str(order.id),
        "checkout-reference": str(settings.PK_PAYTRAIL_MERCHANT_ID),
        "checkout-transaction-id": transaction_id or order.transaction_id,
        "checkout-status": status,
        "checkout-provider": "test-provider",
    }
    if extra:
        params.update(extra)
    params["signature"] = Crypto.calculate_hmac(
        Crypto,
        settings.PK_PAYTRAIL_MERCHANT_SECRET,
        dict(sorted(params.items())),
    )
    return params


class PaytrailSuccessTests(TestCase):
    def setUp(self):
        self.order = make_order()
        self.url = reverse("order:payment_success")

    @patch("pk_paytrail.views.Cart.clear")
    @patch("pk_paytrail.views.async_task")
    def test_valid_callback_marks_order_paid_once(self, async_task_mock, cart_clear_mock):
        params = signed_params(self.order)

        with self.captureOnCommitCallbacks(execute=True):
            first_response = self.client.get(self.url, params)
            second_response = self.client.get(self.url, params)

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(second_response.status_code, 200)
        self.order.refresh_from_db()
        self.assertTrue(self.order.payed)
        self.assertEqual(self.order.status, "processing")
        self.assertEqual(async_task_mock.call_count, 1)
        self.assertEqual(cart_clear_mock.call_count, 2)
        self.assertEqual(first_response.context["ga4_event"]["name"], "purchase")
        self.assertIsNone(second_response.context["ga4_event"])
        self.assertEqual(
            first_response.context["ga4_event"]["params"]["transaction_id"],
            f"DP-{self.order.id}",
        )

    @patch("pk_paytrail.views.async_task")
    def test_signature_covers_new_checkout_parameters(self, async_task_mock):
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.get(
                self.url,
                signed_params(self.order, extra={"checkout-future-field": "value"}),
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(async_task_mock.call_count, 1)

    def test_invalid_amount_is_rejected(self):
        response = self.client.get(
            self.url,
            signed_params(self.order, amount=999),
        )
        self.assertEqual(response.status_code, 403)
        self.order.refresh_from_db()
        self.assertFalse(self.order.payed)

    def test_pending_status_returns_accepted_without_marking_paid(self):
        response = self.client.get(
            self.url,
            signed_params(self.order, status="pending"),
        )
        self.assertEqual(response.status_code, 202)
        self.order.refresh_from_db()
        self.assertFalse(self.order.payed)

    def test_wrong_transaction_is_rejected(self):
        response = self.client.get(
            self.url,
            signed_params(self.order, transaction_id="another-transaction"),
        )
        self.assertEqual(response.status_code, 403)
        self.order.refresh_from_db()
        self.assertFalse(self.order.payed)

    def test_customer_email_is_only_rendered_for_customer_reviews_opt_in(self):
        response = self.client.get(self.url, signed_params(self.order))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["google_customer_reviews"]["email"],
            self.order.email,
        )
        self.assertContains(response, 'id="google-customer-reviews-data"')
        self.assertContains(response, self.order.email, count=1)
        self.assertNotIn(
            self.order.email,
            json.dumps(response.context["ga4_event"]),
        )

        repeat_response = self.client.get(self.url, signed_params(self.order))
        self.assertIsNone(repeat_response.context["google_customer_reviews"])

    def test_enhanced_conversion_requires_prior_ad_user_data_consent(self):
        self.client.cookies["cookie_consent"] = "granted"
        self.client.cookies["cookie_settings"] = quote(
            json.dumps({"ad_user_data": "granted"})
        )

        response = self.client.get(self.url, signed_params(self.order))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["google_ads_enhanced_conversion"]["email"],
            self.order.email,
        )
        self.assertContains(response, 'id="google-ads-enhanced-conversion-data"')

    @override_settings(MERCHANT_SYNC_ENABLED=True)
    @patch("pk_paytrail.views.Cart.clear")
    @patch("pk_paytrail.views.async_task")
    def test_paid_callback_queues_merchant_sync_once(
        self,
        async_task_mock,
        cart_clear_mock,
    ):
        params = signed_params(self.order)

        with self.captureOnCommitCallbacks(execute=True):
            first_response = self.client.get(self.url, params)
            second_response = self.client.get(self.url, params)

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(second_response.status_code, 200)
        task_names = [item.args[0] for item in async_task_mock.call_args_list]
        self.assertEqual(
            task_names.count("shop.tasks.send_order_confirmation_email"),
            1,
        )
        self.assertEqual(
            task_names.count("google_shopping.tasks.sync_order_products"),
            1,
        )


class PaytrailCancelTests(TestCase):
    def setUp(self):
        self.order = make_order()
        self.url = reverse("order:payment_cancel")

    def test_valid_cancel_is_idempotent(self):
        params = signed_params(self.order, status="fail")
        first_response = self.client.get(self.url, params)
        second_response = self.client.get(self.url, params)

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(second_response.status_code, 200)
        self.order.refresh_from_db()
        self.assertFalse(self.order.payed)
        self.assertEqual(self.order.status, "canceled")

    def test_paid_order_cannot_be_cancelled(self):
        self.order.payed = True
        self.order.status = "processing"
        self.order.save()

        response = self.client.get(
            self.url,
            signed_params(self.order, status="fail"),
        )
        self.assertEqual(response.status_code, 403)
        self.order.refresh_from_db()
        self.assertTrue(self.order.payed)
        self.assertEqual(self.order.status, "processing")


class CashOnDeliveryReturnTests(TestCase):
    def setUp(self):
        self.owner = CustomUser.objects.create_user(
            username="cod-owner",
            email="cod-owner@example.test",
            password="test-password",
        )
        self.order = make_order(
            user=self.owner,
            email=self.owner.email,
            payment_method="cod",
            transaction_id="",
            status="processing",
        )
        self.url = reverse("order:payment_success")

    def test_arbitrary_order_id_is_rejected(self):
        response = self.client.get(
            self.url,
            {"order_id": self.order.id, "payment_method": "cod"},
        )
        self.assertEqual(response.status_code, 403)

    @patch("pk_paytrail.views.async_task")
    def test_session_owned_order_is_allowed_and_email_queued_once(self, async_task_mock):
        session = self.client.session
        session["last_order_id"] = self.order.id
        session["cod_confirmation_pending"] = self.order.id
        session.save()

        with self.captureOnCommitCallbacks(execute=True):
            first_response = self.client.get(
                self.url,
                {"order_id": self.order.id, "payment_method": "cod"},
            )
            second_response = self.client.get(
                self.url,
                {"order_id": self.order.id, "payment_method": "cod"},
            )

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(second_response.status_code, 200)
        self.assertEqual(async_task_mock.call_count, 1)
        self.assertEqual(async_task_mock.call_args.args[3], "fi")


class CashOnDeliveryMerchantSyncTests(TestCase):
    @override_settings(MERCHANT_SYNC_ENABLED=True)
    @patch("pk_paytrail.views._queue_order_merchant_sync")
    @patch("pk_paytrail.views.create_order_from_verified_data")
    def test_cod_order_queues_merchant_sync(
        self,
        create_order_mock,
        queue_sync_mock,
    ):
        from pk_paytrail.views import handle_cash_on_delivery

        order = make_order(
            payment_method="cod",
            transaction_id="",
            status="new",
        )
        order.refresh_from_db()
        create_order_mock.return_value = order
        request = SimpleNamespace(session={})
        cart = MagicMock()
        cart.get_total_price.return_value = Decimal("10.00")

        response = handle_cash_on_delivery(
            request,
            MagicMock(),
            {},
            cart,
            "https://testserver",
        )

        self.assertEqual(response.status_code, 200)
        queue_sync_mock.assert_called_once_with(order)
        order.refresh_from_db()
        self.assertEqual(order.status, "processing")
        self.assertEqual(order.payment_method, "cod")
        cart.clear.assert_called_once()
