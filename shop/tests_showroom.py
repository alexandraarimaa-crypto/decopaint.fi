"""Relocation calendar boundaries and display-only release invariants."""
from datetime import date, datetime
from pathlib import Path
import tempfile
from unittest.mock import patch
from zoneinfo import ZoneInfo

from django.template import Context, Engine
from django.test import SimpleTestCase
from django.utils import translation

from scripts.build_relocation_release import BASELINE, ROOT, build
from shop.showroom import showroom_information


class ShowroomTests(SimpleTestCase):
    def test_contact_details_precede_lazy_photos(self):
        with tempfile.TemporaryDirectory() as directory:
            build(directory)
            contact = (Path(directory) / "shop/templates/shop/else/contact.html").read_text()
            self.assertLess(contact.index('id="showroom"'), contact.index('contact1.jpg'))
            self.assertIn('scroll-margin-top:140px', contact)
            self.assertEqual(contact.count('id="showroom"'), 1)

    def test_opening_day_switch_and_permanent_address(self):
        before = showroom_information("fi", date(2026, 11, 30))
        after = showroom_information("fi", date(2026, 12, 1))
        self.assertFalse(before["moved"])
        self.assertIn("suljettu", before["text"])
        self.assertIn("1.12.2026", before["address_label"])
        self.assertTrue(after["moved"])
        self.assertIn("avoinna", after["title"])
        self.assertNotIn("suljettu", after["pickup_notice"])
        self.assertEqual(after["new_street"], "Voivalantie 30")
        later = showroom_information("fi", date(2027, 1, 1))
        self.assertFalse(later["show_banner"])
        self.assertTrue(later["moved"])
        self.assertEqual(later["new_street"], after["new_street"])

    def test_calendar_uses_helsinki_instead_of_visitor_clock(self):
        midnight = datetime(2026, 12, 1, 0, 0, tzinfo=ZoneInfo("Europe/Helsinki"))
        with patch("shop.showroom.datetime") as clock:
            clock.now.return_value = midnight
            self.assertTrue(showroom_information()["moved"])
            self.assertEqual(str(clock.now.call_args.args[0]), "Europe/Helsinki")

    def test_languages_and_online_continuity(self):
        for language, online_word in (("fi", "Verkkokauppa"), ("sv", "Webbutiken"), ("en", "online shop")):
            value = showroom_information(language, date(2026, 11, 17))
            self.assertIn(online_word, value["text"])
            self.assertTrue(value["show_banner"])
            self.assertIn("0400 414 838", value["pickup_notice"])
        self.assertEqual(showroom_information("unknown", date(2026, 11, 17))["title"], "Muutamme 1.12.")

    def test_base_assignment_is_available_in_child_blocks(self):
        engine = Engine(
            libraries={"relocation_tags": "shop.templatetags.relocation_tags"},
            loaders=[("django.template.loaders.locmem.Loader", {
                "base": "{% load relocation_tags %}{% showroom_relocation as showroom %}{% block content %}{% endblock %}",
                "child": '{% extends "base" %}{% block content %}{{ showroom.new_street }} / {{ showroom.online }}{% endblock %}',
            })],
        )
        with translation.override("fi"):
            rendered = engine.get_template("child").render(Context())
        self.assertIn("Voivalantie 30", rendered)
        self.assertIn("Verkkokauppa palvelee normaalisti.", rendered)

    def test_release_preserves_checkout_scripts_and_compiles_templates(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest = build(directory)
            candidate = Path(directory)
            name = "cart/templates/cart/checkout.html"
            old = (BASELINE / name).read_text()
            new = (candidate / name).read_text()
            self.assertEqual(old.split("<script", 1)[1], new.split("<script", 1)[1])
            self.assertEqual((BASELINE / name).read_bytes().split(b"<script", 1)[1], (candidate / name).read_bytes().split(b"<script", 1)[1])
            self.assertIn("{{ showroom.pickup_notice }}", new)
            contact = (candidate / "shop/templates/shop/else/contact.html").read_text()
            self.assertNotIn('id="map"', contact)
            self.assertNotIn("maps.app.goo.gl/wo27", contact)
            self.assertIn("{{ showroom.directions_url }}", contact)
            self.assertEqual(len(manifest["release_files"]), 7)
            for path in manifest["release_files"]:
                if path.endswith(".html"):
                    Engine.get_default().from_string((candidate / path).read_text())
            for name in ("shop/templates/shop/base/base.html", "shop/templates/shop/base/footer.html", "shop/templates/shop/else/contact.html"):
                Engine.get_default().from_string((ROOT / name).read_text())
