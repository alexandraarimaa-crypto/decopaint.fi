import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from django.test import RequestFactory, SimpleTestCase
from django.utils import timezone
from django.template import engines
from scripts.build_sales_flow_release import build


class SalesMeasurementReleaseTests(SimpleTestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.manifest = build(self.root)

    def module(self, filename, name):
        spec = importlib.util.spec_from_file_location(name, self.root / filename)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_measurement_release_leaves_payment_and_feed_code_untouched(self):
        self.assertNotIn("pk_paytrail/views.py", self.manifest["release_files"])
        self.assertNotIn("order/models.py", self.manifest["release_files"])
        self.assertNotIn("google_shopping/tasks.py", self.manifest["release_files"])
        base = (self.root / "shop/templates/shop/base/base.html").read_text()
        self.assertIn("DecoPaintAnalyticsLocation(window.location.href)", base)
        self.assertIn("'ad_storage': isEU ? 'denied'", base)

    def test_all_projected_templates_compile_and_cart_event_is_success_only(self):
        engine = engines["django"].engine
        for name in self.manifest["release_files"]:
            if name.endswith(".html"):
                with self.subTest(template=name):
                    engine.from_string((self.root / name).read_text())
        detail = (self.root / "shop/templates/shop/product/detail.html").read_text()
        self.assertNotIn("track('add_to_cart'", detail)
        self.assertIn('decopaint:price-loading', detail)
        self.assertIn('decopaint:price-ready', detail)
        view = (self.root / "cart/views.py").read_text()
        self.assertGreater(view.index("queue_successful_add(request"), view.index("cart.add("))
        self.assertIn("if not cleaned_data['update']:", view)

    def test_order_capture_stores_canonical_web_identity_only_after_consent(self):
        module = self.module("order/attribution.py", "order.sales_attribution_candidate")
        request = RequestFactory().get("/")
        request.COOKIES = {
            "cookie_settings": json.dumps({"analytics_storage": "granted"}),
            "_ga": "GA1.1.123456789.1793340000",
            "_ga_TESTONLY": "GS2.1.s1793340000$o2$g1$t1793340020$j60",
        }
        result = module.extract_order_attribution(request)
        self.assertEqual(result["ga_client_id"], "123456789.1793340000")
        self.assertEqual(result["ga_session_id"], "1793340000")
        request.COOKIES["cookie_settings"] = json.dumps({"analytics_storage": "denied"})
        result = module.extract_order_attribution(request)
        self.assertNotIn("ga_client_id", result)
        self.assertNotIn("ga_session_id", result)

    def test_measurement_payload_recovers_legacy_envelopes_without_collecting(self):
        module = self.module("order/ga4.py", "order.sales_ga4_candidate")
        order = SimpleNamespace(
            ga_client_id="GA1.1.123456789.1793340000",
            ga_session_id="GS2.1.s1793340000$o2$g1$t1793340020$j60",
            paid_at=timezone.now(), ads_consent="denied",
            ads_personalization_consent="denied",
        )
        with patch.object(module, "build_purchase_event", return_value={
            "name": "purchase", "params": {"transaction_id": "DP-SYNTHETIC", "currency": "EUR", "value": 12.34},
        }), patch.object(module.requests, "post") as post:
            result = module._payload(order)
            self.assertEqual(result["client_id"], "123456789.1793340000")
            self.assertEqual(result["events"][0]["params"]["session_id"], 1793340000)
            self.assertEqual(result["consent"]["ad_user_data"], "DENIED")
            post.assert_not_called()
            order.ga_client_id = "invalid"
            with self.assertRaises(ValueError):
                module._payload(order)
