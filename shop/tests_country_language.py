from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase, override_settings

from shop.language_middleware import CountryDefaultLanguageMiddleware


@override_settings(
    LANGUAGE_CODE="fi",
    LANGUAGES=(("fi", "Finnish"), ("sv", "Swedish"), ("en", "English")),
    LANGUAGE_COOKIE_NAME="django_language",
)
class CountryDefaultLanguageTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = CountryDefaultLanguageMiddleware(lambda request: HttpResponse(request.LANGUAGE_CODE))

    def language_for(self, ip, **meta):
        request = self.factory.get("/", REMOTE_ADDR=ip, **meta)
        request.session = {}
        return self.middleware(request).content.decode()

    def test_finland_defaults_to_finnish(self):
        self.assertEqual(self.language_for("2.58.88.1"), "fi")

    def test_sweden_defaults_to_swedish(self):
        self.assertEqual(self.language_for("2.0.0.1"), "sv")

    def test_other_countries_default_to_english(self):
        self.assertEqual(self.language_for("8.8.8.8"), "en")

    def test_server_country_header_has_priority(self):
        self.assertEqual(
            self.language_for("8.8.8.8", GEOIP_COUNTRY_CODE="SE"),
            "sv",
        )

    def test_non_fi_se_country_header_selects_english(self):
        self.assertEqual(
            self.language_for("2.58.88.1", HTTP_X_COUNTRY_CODE="US"),
            "en",
        )

    def test_manual_cookie_is_never_overridden(self):
        request = self.factory.get("/", REMOTE_ADDR="2.58.88.1")
        request.COOKIES["django_language"] = "en"
        request.session = {}
        self.assertEqual(self.middleware(request).content.decode(), "en")

    def test_search_crawler_keeps_finnish_indexing_language(self):
        self.assertEqual(
            self.language_for("8.8.8.8", HTTP_USER_AGENT="Googlebot/2.1"),
            "fi",
        )
