from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from order.models import Order
from users.models import CustomUser


def make_order(*, user, email):
    return Order.objects.create(
        user=user,
        first_name="Test",
        last_name="Customer",
        email=email,
        address="Testikatu 1",
        postal="00100",
        city="Helsinki",
        phone="0400000000",
        total_price="10.00",
        transaction_id="test-transaction",
    )


class PaymentDetailsAccessTests(TestCase):
    def setUp(self):
        self.owner = CustomUser.objects.create_user(
            username="owner",
            email="owner@example.test",
            password="test-password",
        )
        self.other = CustomUser.objects.create_user(
            username="other",
            email="other@example.test",
            password="test-password",
        )
        self.superuser = CustomUser.objects.create_superuser(
            username="admin",
            email="admin@example.test",
            password="test-password",
        )
        self.order = make_order(user=self.owner, email=self.owner.email)
        self.url = reverse("user:load_payment_details", args=[self.order.id])

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

    def test_other_customer_receives_404(self):
        self.client.force_login(self.other)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    @patch("users.views.get_payment_data", return_value=None)
    def test_owner_can_view_payment_details(self, payment_lookup):
        self.client.force_login(self.owner)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        payment_lookup.assert_called_once_with(self.order.transaction_id)

    @patch("users.views.get_payment_data", return_value=None)
    def test_superuser_can_view_payment_details(self, payment_lookup):
        self.client.force_login(self.superuser)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        payment_lookup.assert_called_once_with(self.order.transaction_id)


class RegistrationEmailTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username="registered",
            email="registered@example.test",
            password="test-password",
        )
        self.url = reverse("user:send_register_email")

    def test_anonymous_request_is_rejected(self):
        response = self.client.post(self.url, {"email": "victim@example.test"})
        self.assertEqual(response.status_code, 302)

    def test_get_is_not_allowed(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    @patch("users.views.send_message")
    def test_message_is_sent_only_to_authenticated_email(self, send_message_mock):
        self.client.force_login(self.user)
        response = self.client.post(self.url, {"email": "victim@example.test"})
        self.assertEqual(response.status_code, 200)
        send_message_mock.assert_called_once()
        self.assertEqual(send_message_mock.call_args.args[0], self.user.email)
