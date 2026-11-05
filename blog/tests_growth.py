import json
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import AnonymousUser
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.test import RequestFactory, TestCase, override_settings
from django.utils.translation import override

from blog.models import BlogPost, Category
from blog.seo import DESCRIPTIONS, enquiry_url, metadata
from shop.models import Product
from shop.templatetags.blog_growth_tags import (
    blog_enquiry_context, blog_list_canonical, product_blog_guides, related_blog_guides,
)


@override_settings(ROOT_URLCONF="blog.tests_urls")
class BlogGrowthTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(name="Kalkkiviimeistely", slug="kalkkiviimeistely")
        cls.other_category = Category.objects.create(name="Muut", slug="muut")
        cls.post = BlogPost.objects.create(
            title="Kalkkimaali, Marmorino vai venetsialainen stucco?",
            slug="kalkkimaali-marmorino-venetsialainen-stucco",
            content="<h2>Valitse pinta</h2><p>Vertaa projektisi materiaaleja.</p>",
            category=cls.category,
        )
        cls.quantity = BlogPost.objects.create(
            title="Kuinka paljon maalia tarvitsen?", slug="kuinka-paljon-maalia-tarvitsen",
            content="<p>Laske pinta-ala ja maalimäärä.</p>", category=cls.other_category,
        )
        cls.product = Product.objects.create(name="Marmorino", slug="marmorino", price=Decimal("10"))
        cls.post.products.add(cls.product)
        cls.quantity.products.add(cls.product)

    def setUp(self):
        self.request = RequestFactory().get("/contact/", secure=True)
        self.request.user = AnonymousUser()

    def test_specific_descriptions_are_unique_and_localized(self):
        for lang in ("fi", "sv", "en"):
            with self.subTest(language=lang), override(lang):
                comparison = metadata(self.post, self.request)
                quantity = metadata(self.quantity, self.request)
                self.assertEqual(comparison["description"], DESCRIPTIONS[self.post.slug][lang])
                self.assertNotEqual(comparison["description"], quantity["description"])
                self.assertLessEqual(len(comparison["description"]), 170)

    def test_fallback_separates_html_blocks_and_excludes_scripts(self):
        self.post.slug = "uusi-opas"
        self.post.content = "<h2>Otsikko</h2><p>Oma &amp; hyödyllinen sisältö.</p><script>hidden()</script>"
        self.assertEqual(metadata(self.post, self.request)["description"], "Otsikko Oma & hyödyllinen sisältö.")
        self.post.content = "<p>pitkä kuvaus </p>" * 100
        self.assertLessEqual(len(metadata(self.post, self.request)["description"]), 170)
        self.post.content = "<script>hidden()</script>"
        self.assertEqual(metadata(self.post, self.request)["description"], self.post.title)

    def test_schema_uses_public_data_and_canonical_without_query(self):
        request = RequestFactory().get(self.post.get_absolute_url() + "?email=private&guide=bad", secure=True)
        self.post.title = '</script><script>alert("bad")</script>'
        data = metadata(self.post, request)
        self.assertNotIn("<", data["schema_json"])
        schema = json.loads(data["schema_json"])
        self.assertEqual(schema["@type"], "BlogPosting")
        self.assertEqual(schema["datePublished"], self.post.created_at.isoformat())
        self.assertEqual(schema["url"], "https://testserver" + self.post.get_absolute_url())
        self.assertNotIn("author", schema)
        self.assertNotIn("dateModified", schema)
        self.assertNotIn("email", data["schema_json"])

    def test_related_guides_use_shared_products_across_categories_and_exclude_self(self):
        unrelated = BlogPost.objects.create(title="Other", slug="other", content="Other", category=self.other_category)
        same_category = BlogPost.objects.create(title="Calce", slug="calce", content="Calce", category=self.category)
        guides = list(related_blog_guides(self.post)["guides"])
        self.assertEqual(guides[0], self.quantity)
        self.assertIn(same_category, guides)
        self.assertNotIn(self.post, guides)
        self.assertNotIn(unrelated, guides)
        self.assertEqual(set(product_blog_guides(self.product)["guides"]), {self.post, self.quantity})

    def test_enquiry_resolves_only_existing_slug_and_contains_no_user_details(self):
        request = RequestFactory().get("/contact/", {"guide": self.post.slug, "email": "private@example.test"})
        context = blog_enquiry_context(request)
        self.assertEqual(context["post"], self.post)
        self.assertIn(self.post.title, context["message"])
        self.assertIn("Pinta-ala", context["message"])
        self.assertNotIn("private@example.test", context["message"])
        self.assertEqual(enquiry_url(self.post), "/contact/?guide=" + self.post.slug + "#project-enquiry")
        for slug in ("missing", "../bad", "<script>", "x" * 201, ""):
            with self.subTest(slug=slug), self.assertNumQueries(1 if slug == "missing" else 0):
                self.assertEqual(blog_enquiry_context(RequestFactory().get("/contact/", {"guide": slug})), {})

    def test_list_canonical_uses_resolved_page_and_drops_arbitrary_query(self):
        paginator = Paginator(range(20), 9)
        request = RequestFactory().get("/blog/?page=2&email=private", secure=True)
        self.assertEqual(blog_list_canonical(request, paginator.page(2)), "https://testserver/blog/?page=2")
        self.assertEqual(blog_list_canonical(request, paginator.page(1)), "https://testserver/blog/")

    @patch("shop.models.Product.total_price", return_value=Decimal("10"))
    def test_article_and_list_render_metadata_links_and_visible_headings(self, _price):
        response = self.client.get(self.post.get_absolute_url() + "?utm_source=test")
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn(DESCRIPTIONS[self.post.slug]["fi"], html)
        self.assertIn('property="og:type" content="article"', html)
        self.assertIn('"@type":"BlogPosting"', html)
        self.assertIn('href="' + self.quantity.get_absolute_url() + '"', html)
        self.assertIn('href="' + enquiry_url(self.post) + '"', html)
        self.assertIn("Valitaan materiaalit", html)
        self.assertEqual(html.count('name="description"'), 1)
        self.assertEqual(html.count('rel="canonical"'), 1)
        listing = self.client.get("/blog/").content.decode()
        self.assertIn("Maalaus- ja sisustusoppaat", listing)

    def test_contact_prefill_is_escaped_and_generic_contact_stays_empty(self):
        BlogPost.objects.filter(pk=self.post.pk).update(title="</textarea><script>alert(1)</script>")
        request = RequestFactory().get("/contact/", {"guide": self.post.slug})
        request.user = AnonymousUser()
        html = render_to_string("shop/else/contact.html", {"request": request}, request=request)
        self.assertIn("&lt;/textarea&gt;&lt;script&gt;", html)
        self.assertIn('id="project-enquiry"', html)
        self.assertIn('name="csrfmiddlewaretoken"', html)
        self.assertNotIn("</textarea><script>alert(1)</script>", html)
        self.assertEqual(blog_enquiry_context(self.request), {})

    def test_empty_product_guide_block_is_omitted(self):
        product = Product.objects.create(name="No guides", slug="no-guides", price=Decimal("10"))
        html = render_to_string("blog/product_guides.html", product_blog_guides(product))
        self.assertNotIn("<h2", html)

    def test_new_interface_text_and_prompt_follow_active_language(self):
        from blog.seo import ui_text
        for lang, heading, prompt in [
            ("fi", "Valitaan materiaalit", "Pinta-ala"),
            ("sv", "Vi hjälper dig", "Yta"),
            ("en", "Choose materials", "Area"),
        ]:
            with self.subTest(language=lang), override(lang):
                self.assertIn(heading, ui_text()["help_title"])
                request = RequestFactory().get("/contact/", {"guide": self.post.slug})
                self.assertIn(prompt, blog_enquiry_context(request)["message"])

    def test_linked_product_renders_its_guide_links(self):
        html = render_to_string("blog/product_guides.html", product_blog_guides(self.product))
        self.assertIn(self.post.get_absolute_url(), html)
        self.assertIn(self.quantity.get_absolute_url(), html)

    def test_all_curated_descriptions_are_unique_bounded_and_available_in_three_languages(self):
        for lang in ("fi", "sv", "en"):
            values = [record[lang] for record in DESCRIPTIONS.values()]
            self.assertEqual(len(values), len(set(values)))
            self.assertTrue(all(60 <= len(value) <= 170 for value in values))
