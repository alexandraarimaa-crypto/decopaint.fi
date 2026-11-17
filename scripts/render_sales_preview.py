"""Render the actual new fragments with synthetic data; no DB or integrations."""
import os
from pathlib import Path
import sys
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.test_settings")
import django
django.setup()
from django.template.loader import render_to_string
from django.test import override_settings
from django.urls import include, path

def main(output):
    directory = Path(output)
    directory.mkdir(parents=True, exist_ok=True)
    # URL reversal only; do not import production views or make network calls.
    preview_patterns = [
        path("contact/", lambda request: None, name="contact"),
        path("catalog/<slug:category_slug>/", lambda request: None, name="product_list_by_category"),
    ]
    preview_urlconf = ModuleType("sales_preview_urls")
    preview_urlconf.urlpatterns = [path("", include((preview_patterns, "shop")))]
    with override_settings(ROOT_URLCONF=preview_urlconf):
        catalogue = render_to_string("shop/product/sales_catalogue.html", {})
    html = '''<!doctype html><html lang="fi"><head><meta charset="utf-8"><meta name="robots" content="noindex,nofollow"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Synthetic sales-flow preview</title><link rel="stylesheet" href="/static/assets/css/sales-flow.css"><style>body{font:16px/1.55 system-ui;margin:0 auto;max-width:1050px;padding:20px}button,select,input{font:inherit}button{padding:12px;cursor:pointer}button:disabled{opacity:.5}h1{font-size:28px}.small{font-size:14px}</style></head><body><h1>Materiaalin valinta — suljettu testi</h1><p>Synteettiset tuotteet. Ei maksuja, tilauksia tai analytiikkalähetyksiä.</p>'''
    html += catalogue + '<form id="cart_form"><label>Pakkauskoko <select id="preview-size"><option value="5 kg">5 kg</option><option value="20 kg">20 kg</option><option value="invalid">Virheellinen vaihtoehto (testi)</option></select></label>'
    html += '<label>Määrä <input id="quantity" type="number" min="1" value="1"></label> <button type="submit">Lisää koriin</button><p id="preview-status" role="status"></p></form>'
    html += '''<section class="dp-sales-box"><h2>Toimitusarvio kassalla</h2><p>Tilaustuote</p><p class="dp-sales-delivery">Toimitusaika noin 2–4 viikkoa. Tarkka lähetysarvio säilyy näkyvissä.</p></section><script>document.addEventListener('DOMContentLoaded',function(){var size=document.getElementById('preview-size');function ready(){document.dispatchEvent(new Event('decopaint:price-loading'));if(size.value!=='invalid')document.dispatchEvent(new CustomEvent('decopaint:price-ready',{detail:{size:size.value,price:size.value==='5 kg'?49.32:178.56}}));}size.addEventListener('change',ready);document.getElementById('quantity').addEventListener('change',ready);document.getElementById('cart_form').addEventListener('submit',function(e){var blocked=e.defaultPrevented;e.preventDefault();if(blocked)return;document.getElementById('preview-status').textContent='Synteettinen testi: määrä '+document.getElementById('quantity').value;});setTimeout(ready,0);});</script></body></html>'''
    (directory / "index.html").write_text(html, encoding="utf-8")
    import shutil
    for relative in ["assets/css/sales-flow.css", "assets/js/sales-product.js"]:
        target = directory / "static" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / "shop/static" / relative, target)
    print("Rendered synthetic preview; no database read/write, email, analytics or payment request.")


if __name__ == "__main__":
    main(sys.argv[1])
