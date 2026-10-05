from pathlib import Path
from decimal import Decimal
import json
from types import SimpleNamespace
from unittest.mock import patch

from django.conf import settings
from django.test import Client, RequestFactory, SimpleTestCase, TestCase

from shop import views
from shop.models import Category, Product, Tag
from shop.seo import (
    CATALOG_SEO,
    CATEGORY_SEO,
    HOME_SEO,
    PRODUCT_SEO,
    TAG_CATEGORY_REDIRECTS,
    build_canonical,
    category_seo,
    product_seo,
)
from shop.sitemaps import VirtualCategorySitemap
from shop.product_schema import build_product_data, clean_text, json_for_script


class SeoMetadataTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_canonical_drops_tracking_and_product_option_parameters(self):
        request = self.factory.get(
            "/product/marmorino-naturale/",
            {"utm_source": "ads", "page": "19", "size": "5-kg"},
            HTTP_HOST="testserver",
        )
        self.assertEqual(
            build_canonical(request),
            "http://testserver/product/marmorino-naturale/",
        )

    def test_pagination_canonical_keeps_only_non_first_page(self):
        page_two = self.factory.get(
            "/catalog/sisustusmaali/",
            {"page": "2", "utm_source": "ads"},
            HTTP_HOST="testserver",
        )
        first_page = self.factory.get(
            "/catalog/sisustusmaali/",
            {"page": "1"},
            HTTP_HOST="testserver",
        )
        self.assertEqual(
            build_canonical(page_two, keep_query=("page",)),
            "http://testserver/catalog/sisustusmaali/?page=2",
        )
        self.assertEqual(
            build_canonical(first_page, keep_query=("page",)),
            "http://testserver/catalog/sisustusmaali/",
        )

    def test_metadata_is_bounded_unique_and_not_keyword_stuffed(self):
        records = [HOME_SEO, CATALOG_SEO]
        records.extend(CATEGORY_SEO.values())
        records.extend(PRODUCT_SEO.values())

        titles = []
        for record in records:
            title = record["title"]
            description = record["description"]
            self.assertLessEqual(len(title), 65, title)
            self.assertLessEqual(len(description), 180, description)
            self.assertNotIn("mikrosementti", description.lower())
            self.assertNotIn("märkätilaan", description.lower())
            titles.append(title)

        self.assertEqual(len(titles), len(set(titles)))

    def test_fallback_metadata_is_escaped_and_trimmed(self):
        category = category_seo("unknown", "Pitkä tuoteryhmän nimi")
        product = product_seo(
            "unknown",
            "OIKOS Testituote",
            "<p>Vahvistettu näkyvä kuvaus ilman uutta teknistä väitettä.</p>",
        )
        self.assertLessEqual(len(category["title"]), 60)
        self.assertNotIn("<p>", product["description"])

    def test_duplicate_high_signal_tags_redirect_permanently(self):
        for tag_slug, category_slug in TAG_CATEGORY_REDIRECTS.items():
            request = self.factory.get(f"/catalog/tag/{tag_slug}/")
            sentinel = object()
            with patch("shop.views.redirect", return_value=sentinel) as redirect_mock:
                response = views.product_list_by_tag(request, tag_slug)
            self.assertIs(response, sentinel)
            redirect_mock.assert_called_once_with(
                "shop:product_list_by_category",
                category_slug=category_slug,
                permanent=True,
            )

    def test_virtual_exterior_category_is_in_sitemap(self):
        self.assertEqual(VirtualCategorySitemap().items(), ["ulkomaalit"])


class ProductStructuredDataTests(SimpleTestCase):
    def setUp(self):
        self.request = RequestFactory().get(
            "/product/testituote/", HTTP_HOST="testserver", secure=True
        )
        self.product = SimpleNamespace(
            sku="TEST-001",
            thumbnail=SimpleNamespace(url="/media/products/test.jpg"),
            image=None,
        )

    def test_general_product_has_no_unresolved_offer(self):
        data = build_product_data(
            request=self.request,
            product=self.product,
            name="OIKOS Testituote",
            description="<p>Vahvistettu kuvaus.</p>",
            canonical_url="https://decopaint.fi/product/testituote/",
        )
        self.assertEqual(data["@type"], "Product")
        self.assertEqual(data["brand"]["name"], "OIKOS")
        self.assertEqual(
            data["image"], ["https://testserver/media/products/test.jpg"]
        )
        self.assertNotIn("offers", data)

    def test_resolved_variant_offer_uses_public_price_and_real_availability(self):
        variant = SimpleNamespace(
            item_code="VAR-25",
            order_item=True,
            total_price=lambda _user: Decimal("30.72"),
        )
        data = build_product_data(
            request=self.request,
            product=self.product,
            name="OIKOS Testituote",
            description="Tekninen kuvaus",
            canonical_url="https://decopaint.fi/product/testituote/",
            variant=variant,
            selection={"size": "0.25 L"},
        )
        offer = data["offers"]
        self.assertEqual(offer["price"], "30.72")
        self.assertEqual(offer["availability"], "https://schema.org/PreOrder")
        self.assertEqual(offer["sku"], "VAR-25")
        self.assertEqual(
            offer["url"],
            "https://decopaint.fi/product/testituote/?size=0.25+L",
        )

    def test_json_script_escaping_blocks_markup_injection(self):
        payload = {"description": "</script><script>alert(1)</script>&"}
        rendered = json_for_script(payload)
        self.assertNotIn("<", rendered)
        self.assertNotIn(">", rendered)
        self.assertNotIn("&", rendered)
        self.assertEqual(json.loads(rendered), payload)
        self.assertEqual(clean_text("<p>A&nbsp; B</p>"), "A B")


class SeoTemplateContractTests(SimpleTestCase):
    def read(self, relative_path):
        return (Path(settings.BASE_DIR) / relative_path).read_text(encoding="utf-8")

    def test_base_template_has_language_unique_meta_and_safe_canonical(self):
        template = self.read("shop/templates/shop/base/base.html")
        self.assertIn('lang="{{ current_language|default:\'fi\' }}"', template)
        self.assertIn('name="description" content="{{ seo.description', template)
        self.assertIn('name="robots" content="{{ seo_robots', template)
        self.assertNotIn('name="keywords"', template)
        self.assertNotIn('href="{{ request.build_absolute_uri }}"', template)
        self.assertIn("{{ request.path }}", template)
        self.assertIn("{% block open_graph %}", template)
        self.assertIn("{% block schema_markup %}", template)

    def test_primary_templates_use_seo_titles_and_single_category_h1_contract(self):
        homepage = self.read("shop/templates/shop/else/main.html")
        category = self.read("shop/templates/shop/product/list.html")
        product = self.read("shop/templates/shop/product/detail.html")

        self.assertIn("{% block title %}{{ seo.title }}{% endblock %}", homepage)
        self.assertIn("{% if seo.h1 %}{{ seo.h1 }}{% elif category %}", category)
        self.assertNotIn("default:category.name", category)
        self.assertNotIn("</h4>", category)
        self.assertIn("{{ seo.h1 }}", product)
        self.assertIn('content="{{ canonical_url }}"', product)
        self.assertIn('property="og:type" content="product"', product)
        self.assertIn('id="product-structured-data"', product)
        self.assertNotIn('"description": " {{ product.description|safe }}"', product)
        self.assertNotIn('"availability": "https://schema.org/InStock"', product)

    def test_homepage_primary_links_do_not_point_to_duplicate_tags(self):
        homepage = self.read("shop/templates/shop/else/main.html")
        for tag_slug in TAG_CATEGORY_REDIRECTS:
            self.assertNotIn(f"tag_slug='{tag_slug}'", homepage)

    def test_catalog_view_supplies_explicit_empty_category(self):
        views_source = self.read("shop/views.py")
        all_products_source = views_source.split("def all_products", 1)[1].split(
            "def product_list", 1
        )[0]
        self.assertIn("'category': None", all_products_source)


class SeoViewSmokeTests(TestCase):
    def setUp(self):
        self.client = Client()

    def assert_seo_page(self, response):
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<html lang=", html=False)
        self.assertContains(response, 'rel="canonical"', html=False)

    def test_catalog_and_p0_category_pages_render(self):
        self.assert_seo_page(self.client.get("/catalog/", secure=True))

        for slug, seo in CATEGORY_SEO.items():
            if slug == "ulkomaalit":
                continue
            Category.objects.create(name=seo["h1"], slug=slug)

        for slug in CATEGORY_SEO:
            if slug == "ulkomaalit":
                continue
            with self.subTest(slug=slug):
                self.assert_seo_page(
                    self.client.get(f"/catalog/{slug}/", secure=True)
                )

    def test_virtual_exterior_category_renders_from_verified_tag(self):
        Tag.objects.create(name="Ulkomaalit", slug="ulkomaalit")
        response = self.client.get("/catalog/ulkomaalit/", secure=True)
        self.assert_seo_page(response)
        self.assertContains(response, CATEGORY_SEO["ulkomaalit"]["h1"])

    @patch.object(Product, "total_price", return_value=Decimal("10.00"))
    def test_p0_products_render_with_clean_canonical(self, _total_price):
        for slug, seo in PRODUCT_SEO.items():
            Product.objects.create(name=seo["h1"], slug=slug, price=Decimal("10.00"))

        for slug, seo in PRODUCT_SEO.items():
            with self.subTest(slug=slug):
                with patch("shop.views._resolve_variant") as resolve_variant:
                    response = self.client.get(
                        f"/product/{slug}/?utm_source=qa&size=5-kg",
                        secure=True,
                    )
                resolve_variant.assert_not_called()
                self.assert_seo_page(response)
                self.assertContains(response, seo["title"])
                self.assertContains(
                    response,
                    f'href="https://testserver/product/{slug}/"',
                    html=False,
                )
                self.assertContains(
                    response,
                    'property="og:type" content="product"',
                    html=False,
                    count=1,
                )
                html = response.content.decode("utf-8")
                marker = '<script id="product-structured-data" type="application/ld+json">'
                self.assertEqual(html.count(marker), 1)
                structured_json = html.split(marker, 1)[1].split("</script>", 1)[0]
                structured_data = json.loads(structured_json)
                self.assertEqual(structured_data["@type"], "Product")
                self.assertNotIn("offers", structured_data)

    def test_duplicate_tag_urls_redirect_to_canonical_categories(self):
        for tag_slug, category_slug in TAG_CATEGORY_REDIRECTS.items():
            with self.subTest(tag_slug=tag_slug):
                response = self.client.get(
                    f"/catalog/tag/{tag_slug}/",
                    secure=True,
                )
                self.assertEqual(response.status_code, 301)
                self.assertTrue(
                    response["Location"].endswith(f"/catalog/{category_slug}/"),
                    response["Location"],
                )
