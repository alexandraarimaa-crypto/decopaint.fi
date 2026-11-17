"""Project the display-only relocation change onto audited current templates."""
import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "deployments/relocation-20261117/baseline"
TEMPLATES = [
    "shop/templates/shop/base/base.html",
    "shop/templates/shop/base/footer.html",
    "shop/templates/shop/else/contact.html",
    "cart/templates/cart/checkout.html",
]
NEW_FILES = [
    "shop/showroom.py", "shop/templatetags/relocation_tags.py",
    "shop/templates/shop/base/relocation_notice.html",
]


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise ValueError("Expected one relocation anchor: " + old[:80])
    return text.replace(old, new, 1)


def contact_details_first(text):
    """Keep the directions anchor ahead of legacy photos that change height."""
    match = re.search(r'<section id="showroom">.*?</section>', text, flags=re.S)
    if not match:
        raise ValueError("Expected the showroom contact section")
    details = match[0].replace('<section id="showroom">', '<section class="pb-12">', 1)
    details = replace_once(details, '<div class="row">', '<div class="row" id="showroom" style="scroll-margin-top:140px;">')
    gallery = '<section class="mb-13 px-8">'
    if text.index(gallery) > match.start():
        raise ValueError("Contact section order differs from the audited layout")
    text = replace_once(text, match[0], '')
    return replace_once(text, gallery, details + '\n\n' + gallery)


def project(name, text):
    newline = "\r\n" if text.count("\r\n") > text.count("\n") / 2 else "\n"
    if name.endswith("base/base.html"):
        text = replace_once(text, "{% load static analytics_tags i18n %}", "{% load static analytics_tags i18n relocation_tags %}")
        text = replace_once(text, "{% get_current_language as current_language %}", "{% get_current_language as current_language %}" + newline + "{% showroom_relocation as showroom %}")
        text = replace_once(text, '<main id="content" class="wrapper layout-page">', '<main id="content" class="wrapper layout-page">' + newline + '{% include "shop/base/relocation_notice.html" %}')
    elif name.endswith("base/footer.html"):
        old = '{% translate "Asessorinkatu 12" %}<br>{% translate "20780 Kaarina" %}'
        new = '{{ showroom.address_label }}<br>{{ showroom.new_street }}<br>{{ showroom.postcode_city }}'
        if old in text:
            text = replace_once(text, old, new)
        else:
            text = replace_once(text, "Asessorinkatu 12, 20780 Kaarina<br>", new + "<br>")
    elif name.endswith("else/contact.html"):
        text, count = re.subn(r'<section>\r?\n\r?\n  <div class="container">', lambda match: match[0].replace('<section>', '<section id="showroom">'), text)
        if count != 1:
            raise ValueError("Contact showroom anchor changed")
        pattern = r'(?:{% translate "Asessorinkatu 12" %}|Asessorinkatu 12)<br>\s*(?:{% translate "20780 Kaarina" %}|20780 Kaarina)'
        text, count = re.subn(pattern, '{{ showroom.address_label }}<br><strong>{{ showroom.new_street }}<br>{{ showroom.postcode_city }}</strong>{% if not showroom.moved %}<br>{{ showroom.old_location }}{% endif %}', text)
        if count != 1:
            raise ValueError("Contact address anchor changed")
        text = replace_once(text, 'href="https://maps.app.goo.gl/wo27UgDj9JZRmNYq7" target="_blank"', 'href="{{ showroom.directions_url }}" target="_blank" rel="noopener noreferrer"')
        text = text.replace('{% translate "Reittiohjeet" %}', '{{ showroom.map_label }}').replace('>Reittiohjeet</a>', '>{{ showroom.map_label }}</a>')
        hours = '<h3 class="fs-5 mb-4">{{ showroom.hours_title }}</h3>{% if not showroom.moved %}<p><strong>{{ showroom.closed }}</strong></p>{% endif %}<p>{{ showroom.weekdays }}: 9:00–17:00<br>{{ showroom.weekend }}: {{ showroom.appointment }}</p><p>{{ showroom.online }}</p>'
        text = replace_once(text, '{{ open_time|safe }}', hours)
        map_pattern = r'(?:{% if mapbox_public_token %}\s*)?<section class="pt-9 pt-md-16 pt-lg-18">.*?</section>(?:\s*{% endif %})?'
        text, count = re.subn(map_pattern, '', text, flags=re.S)
        if count != 1:
            raise ValueError("Contact map anchor changed")
        # Remove only the old map script; do not leave a pin at the old premises.
        text, count = re.subn(r'{% block javascript %}.*?{% endblock %}', '', text, flags=re.S)
        if count != 1:
            raise ValueError("Contact map script anchor changed")
        text = contact_details_first(text)
    elif name.endswith("cart/checkout.html"):
        anchor = '<strong>{% translate "Nouto myymälästä" %}</strong><br>'
        if anchor not in text:
            anchor = '<strong>Nouto myymälästä</strong><br>'
        text = replace_once(text, anchor, anchor + newline + '                                        <span class="d-block mt-2 mb-2" style="max-width:42rem;font-size:.9rem;line-height:1.5;">{{ showroom.pickup_notice }}</span>')
    else:
        raise ValueError("Unrecognized relocation target: " + name)
    return text


def build(output):
    output = Path(output)
    audit = json.loads((BASELINE.parent / "runtime-source-manifest.json").read_text())
    expected = audit["production_sha256"]
    manifest = {"release_files": TEMPLATES + NEW_FILES, "expected_production_sha256": {}, "sha256": {}}
    for name in manifest["release_files"]:
        if name in TEMPLATES:
            raw = (BASELINE / name).read_bytes()
            if hashlib.sha256(raw).hexdigest() != audit["baseline_sha256"][name]:
                raise ValueError("Audited baseline hash mismatch: " + name)
            content = project(name, raw.decode("utf-8")).encode("utf-8")
            manifest["expected_production_sha256"][name] = expected[name]
        else:
            content = (ROOT / name).read_bytes()
            manifest["expected_production_sha256"][name] = None
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        manifest["sha256"][name] = hashlib.sha256(content).hexdigest()
    (output / "sales-flow-release.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    build(parser.parse_args().output)
    print("Built seven guarded display-only files; no database or static publication operation.")
