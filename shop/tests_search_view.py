import json
import tempfile
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from django.http import HttpResponse
from django.test import RequestFactory, TestCase, override_settings

from shop.models import Product
from shop.search_engine import load_search_index
from shop.views import search_results


def search_record(slug, name, product_type, surfaces):
    return {
        "slug": slug,
        "product": name,
        "keywords": {
            "exact_and_name_variants": [name],
            "brands": ["oikos"],
            "product_types": [product_type],
            "purposes": ["pohjustus"],
            "surfaces": surfaces,
            "scope": [],
            "methods": [],
            "controlled_misspellings": [],
        },
        "technical_filters": {
            "purposes": ["pohjustus"],
            "compatible_surfaces": surfaces,
            "scope": [],
            "application_methods": [],
        },
    }


class SearchResultsViewTests(TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.index_path = Path(self.temp_dir.name) / "index.json"
        self.overrides_path = Path(self.temp_dir.name) / "overrides.json"
        self.index_path.write_text(
            json.dumps(
                [
                    search_record(
                        "pvc-primer",
                        "Tartuntapohjamaali PVC Primer",
                        "tartuntapohjamaali",
                        ["PVC"],
                    ),
                    search_record(
                        "metal-primer",
                        "Ruosteenestoaine Metal Primer",
                        "ruosteenestoaine",
                        ["metalli"],
                    ),
                    search_record(
                        "hidden-pvc-primer",
                        "Poistunut PVC Pohjamaali",
                        "pohjamaali",
                        ["PVC"],
                    ),
                ]
            ),
            encoding="utf-8",
        )
        self.overrides_path.write_text('{"products": {}}', encoding="utf-8")
        Product.objects.create(
            name="Tartuntapohjamaali PVC Primer",
            slug="pvc-primer",
            price=Decimal("10.00"),
            available=True,
        )
        Product.objects.create(
            name="Ruosteenestoaine Metal Primer",
            slug="metal-primer",
            price=Decimal("10.00"),
            available=True,
        )
        Product.objects.create(
            name="Poistunut PVC Pohjamaali",
            slug="hidden-pvc-primer",
            price=Decimal("10.00"),
            available=False,
        )
        self.factory = RequestFactory()
        load_search_index.cache_clear()

    def tearDown(self):
        load_search_index.cache_clear()
        self.temp_dir.cleanup()

    def test_view_returns_only_available_technically_matching_products(self):
        request = self.factory.get("/catalog/search/", {"q": "PVC pohjamaali"})
        with override_settings(
            PRODUCT_SEARCH_INDEX_PATH=self.index_path,
            PRODUCT_SEARCH_OVERRIDES_PATH=self.overrides_path,
        ), patch("shop.views.render", return_value=HttpResponse("ok")) as render_mock:
            response = search_results(request)

        self.assertEqual(response.status_code, 200)
        context = render_mock.call_args.args[2]
        self.assertEqual(context["results_count"], 1)
        self.assertEqual(
            [product.slug for product in context["results"]], ["pvc-primer"]
        )

    def test_ajax_uses_the_same_ranked_and_filtered_results(self):
        request = self.factory.get(
            "/catalog/search/",
            {"q": "PVC pohjamaali"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        with override_settings(
            PRODUCT_SEARCH_INDEX_PATH=self.index_path,
            PRODUCT_SEARCH_OVERRIDES_PATH=self.overrides_path,
        ), patch("shop.views.render", return_value=HttpResponse("ok")) as render_mock:
            response = search_results(request)

        self.assertEqual(response.status_code, 200)
        context = render_mock.call_args.args[2]
        self.assertEqual(context["results_count"], 1)
        self.assertEqual([product.slug for product in context["results"]], ["pvc-primer"])
