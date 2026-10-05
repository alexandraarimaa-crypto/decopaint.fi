from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from shop.order_email import build_order_email_context, normalize_email_language


class OrderEmailLocalizationTests(SimpleTestCase):
    def _order(self, **overrides):
        values = {
            "shipping_method": "pickup",
            "payment_method": "cod",
            "address": "Customer street 1",
            "postal": "00100",
            "city": "Helsinki",
            "get_shipping_method_display": lambda: "Nouto myymälästä",
            "get_payment_method_display": lambda: "Maksaa noudettaessa",
        }
        values.update(overrides)
        return SimpleNamespace(**values)

    def test_swedish_pickup_uses_store_location_and_pickup_payment(self):
        context = build_order_email_context(self._order(), "/orders/2261/", "sv")

        self.assertEqual(context["email_language"], "sv")
        self.assertEqual(context["copy"]["subject"], "Orderbekräftelse – Deco Paint")
        self.assertEqual(context["address_label"], "Upphämtningsplats")
        self.assertEqual(
            context["address_value"],
            "Deco Paint Finland Oy, Asessorinkatu 12, 20780 Kaarina",
        )
        self.assertEqual(context["shipping_method_label"], "Hämtning i butik")
        self.assertEqual(context["payment_method_label"], "Betalas vid upphämtning")

    def test_delivery_order_keeps_customer_delivery_address(self):
        context = build_order_email_context(
            self._order(shipping_method="weight_based", payment_method="online"),
            "/orders/1/",
            "en",
        )

        self.assertEqual(context["address_label"], "Delivery address")
        self.assertEqual(context["address_value"], "Customer street 1, 00100 Helsinki")
        self.assertEqual(context["payment_method_label"], "Online payment")

    def test_regional_and_unknown_codes_are_normalized(self):
        self.assertEqual(normalize_email_language("sv-SE"), "sv")
        self.assertEqual(normalize_email_language("en_US"), "en")
        self.assertEqual(normalize_email_language("de"), "fi")


class SynchronousMailTests(SimpleTestCase):
    def test_queued_mail_backend_uses_local_mail_server(self):
        from mail.backends import LocalSMTPEmailBackend

        backend = LocalSMTPEmailBackend()

        self.assertEqual(backend.host, "localhost")
        self.assertEqual(backend.port, 25)
        self.assertEqual(backend.username, "")
        self.assertEqual(backend.password, "")
        self.assertFalse(backend.use_tls)
        self.assertFalse(backend.use_ssl)
        self.assertEqual(backend.timeout, 30)

    @patch("mail.views.get_connection")
    def test_direct_delivery_uses_local_mail_server(self, get_connection_mock):
        from mail.views import _smtp_connection

        _smtp_connection()

        get_connection_mock.assert_called_once_with(
            backend="django.core.mail.backends.smtp.EmailBackend",
            host="localhost",
            port=25,
            username="",
            password="",
            use_tls=False,
            use_ssl=False,
            timeout=30,
        )

    @patch("mail.views._attach_brand_logo")
    @patch("mail.views.EmailMultiAlternatives")
    @patch("mail.views._smtp_connection")
    @patch("mail.views.render_to_string", return_value="<p>Order</p>")
    def test_synchronous_delivery_uses_real_smtp_connection(
        self,
        render_mock,
        connection_mock,
        email_class_mock,
        logo_mock,
    ):
        from mail.views import send_message

        smtp_connection = MagicMock()
        connection_mock.return_value = smtp_connection
        email = email_class_mock.return_value
        email.send.return_value = 1

        sent = send_message(
            "customer@example.test",
            "Order confirmation",
            "purchase_confirmation.html",
            synchronous=True,
        )

        self.assertTrue(sent)
        email_class_mock.assert_called_once_with(
            subject="Order confirmation",
            body="Order",
            from_email="Deco Paint Finland Oy <tests@invalid.example>",
            to=["customer@example.test"],
            connection=smtp_connection,
            reply_to=["info@decopaint.fi"],
        )
        self.assertEqual(email.encoding, "utf-8")
        email.attach_alternative.assert_called_once_with("<p>Order</p>", "text/html")
        email.send.assert_called_once_with()

    @patch("mail.views._attach_brand_logo")
    @patch("mail.views.EmailMultiAlternatives")
    @patch("mail.views.render_to_string")
    def test_status_email_keeps_finnish_letters_in_utf8_mime(
        self,
        render_mock,
        email_class_mock,
        logo_mock,
    ):
        from mail.views import send_message

        render_mock.return_value = (
            "<p>tilauksenne <b>#2261</b> on <b>Lähetetty</b>.</p>"
        )
        email = email_class_mock.return_value
        email.send.return_value = 1

        sent = send_message(
            "customer@example.test",
            "Tilaus #2261 on Lähetetty",
            "order_status_change.html",
        )

        self.assertTrue(sent)
        email_class_mock.assert_called_once_with(
            subject="Tilaus #2261 on Lähetetty",
            body="tilauksenne #2261 on Lähetetty.",
            from_email="Deco Paint Finland Oy <tests@invalid.example>",
            to=["customer@example.test"],
            connection=None,
            reply_to=["info@decopaint.fi"],
        )
        self.assertEqual(email.encoding, "utf-8")
        email.attach_alternative.assert_called_once_with(
            "<p>tilauksenne <b>#2261</b> on <b>Lähetetty</b>.</p>",
            "text/html",
        )
        email.send.assert_called_once_with()
