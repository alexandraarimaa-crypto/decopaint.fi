from django.test import SimpleTestCase
from django.urls import resolve


class LegacyRedirectTests(SimpleTestCase):
    def test_product_redirect_is_permanent_and_preserves_query_string(self):
        response = self.client.get("/product/1-primer/?gclid=test&utm_source=google")

        self.assertEqual(response.status_code, 301)
        self.assertEqual(
            response["Location"],
            "/product/il-primer/?gclid=test&utm_source=google",
        )

    def test_contact_redirect_is_permanent(self):
        response = self.client.get("/yhteystiedot")

        self.assertRedirects(
            response,
            "/contact/",
            status_code=301,
            fetch_redirect_response=False,
        )

    def test_cart_root_resolves_to_cart_detail(self):
        match = resolve("/cart/")

        self.assertEqual(match.view_name, "cart:cart_detail")
