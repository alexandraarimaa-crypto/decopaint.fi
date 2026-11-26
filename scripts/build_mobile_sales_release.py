"""Build only the mobile-menu template, preserving audited live translations/auth."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAME = 'shop/templates/shop/base/modal.html'
BASELINE = ROOT / 'deployments/mobile-tarjoukset-20261126/baseline' / NAME
EXPECTED = '70a7ea1df3769f5b2127c710704c82044c0e49c0fb469c50c7c2969c326bad15'


def build(output):
    original = BASELINE.read_bytes()
    if hashlib.sha256(original).hexdigest() != EXPECTED:
        raise ValueError('Audited live menu baseline changed')
    source = original.decode('utf-8')
    for number, label in [(8, 'Yhteystiedot'), (7, 'Toimitus ja palautukset'),
                          (6, 'Ideat ja ohjeet'), (5, 'Palvelut'),
                          (4, 'Kurssit'), (3, 'Ammattilaisille')]:
        old = '<small>%02d</small> {%% translate "%s" %%}' % (number, label)
        if source.count(old) != 1:
            raise ValueError('Live menu item changed: ' + label)
        source = source.replace(old, old.replace('%02d' % number, '%02d' % (number + 1), 1), 1)
    anchor = '''                            <li class="nav-item">
                                <a class="nav-link text-dark"
                                    href="{% url 'b2b:start' %}"><span><small>04</small> {% translate "Ammattilaisille" %}</span></a>
                            </li>'''
    if source.count(anchor) != 1:
        raise ValueError('Live menu insertion anchor changed')
    addition = '''                            <li class="nav-item">
                                <a class="nav-link text-dark"
                                    href="{% url 'shop:product_list_by_category' category_slug='tarjoukset' %}"><span><small>03</small> {% translate "Tarjoukset" %}</span></a>
                            </li>

'''
    source = source.replace(anchor, addition + anchor, 1)
    output = Path(output)
    dest = output / NAME
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(source.encode('utf-8'))
    manifest = {
        'release_files': [NAME],
        'sha256': {NAME: hashlib.sha256(dest.read_bytes()).hexdigest()},
        'expected_production_sha256': {NAME: EXPECTED},
    }
    (output / 'sales-flow-release.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    print(json.dumps(build(parser.parse_args().output)))
