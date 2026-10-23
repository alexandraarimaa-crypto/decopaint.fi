"""Build a scoped release while preserving the audited deployed storefront.

No server access, credentials, product data or database operations. The runtime
baseline is source-controlled because production differs from the recovered
repository. Only the manual information is added to these deployed files.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / 'deployments/manual-variant-info-20261023/baseline'


def replace_once(source, old, new):
    if source.count(old) != 1:
        raise ValueError('Audited runtime anchor changed: ' + old[:90])
    return source.replace(old, new, 1)


def build(output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    paths = [
        'shop/models.py', 'shop/admin.py',
        'shop/migrations/0060_attribute_a_class_en_attribute_a_class_fi_and_more.py',
        'shop/migrations/0061_variant_material_info.py',
        'shop/static/assets/js/variant-material-info.js',
        'shop/templates/admin/shop/variant_material_info.html',
        'shop/templatetags/variant_material_info_tags.py',
    ]
    for name in paths:
        dest = output / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, dest)

    views = (BASELINE / 'shop/views.py').read_text()
    views = replace_once(
        views, "                'is_asiakas_group': is_asiakas_group\n",
        "                'is_asiakas_group': is_asiakas_group,\n"
        "                'price_per_m2': str(variant.price_per_m2) if variant.price_per_m2 is not None else None,\n"
        "                'coverage_m2': variant.coverage_m2,\n",
    )
    (output / 'shop/views.py').write_text(views)
    paths.append('shop/views.py')

    detail = (BASELINE / 'shop/templates/shop/product/detail.html').read_text()
    changes = [
        ('    <script>\n    $(document).ready(function () {\n        // Global price management variables',
         '    <script src="{% static \'assets/js/variant-material-info.js\' %}"></script>\n    <script>\n    $(document).ready(function () {\n        // Global price management variables'),
        ("        function showPriceLoading() {\n            $('#price-container').hide();",
         "        function showPriceLoading() {\n            window.updateVariantMaterialInfo();\n            $('#price-container').hide();"),
        ('        function updatePrice() {\n            if (priceLoading) {',
         '        function updatePrice() {\n            window.updateVariantMaterialInfo();\n            if (priceLoading) {'),
        ('                    if (data.price !== undefined) {\n                        var unit_price',
         '                    if (data.price !== undefined) {\n                        if (!pendingPriceUpdate) {\n                            window.updateVariantMaterialInfo(data);\n                        }\n                        var unit_price'),
        ('            <span class="fw-semibold text-body-emphasis me-7">{% translate "Koko:" %} </span>',
         '            <div class="d-flex align-items-baseline flex-wrap gap-2">\n              <span class="fw-semibold text-body-emphasis me-7">{% translate "Koko:" %} </span>\n              <small id="variant-coverage" class="text-muted" aria-live="polite" hidden></small>\n            </div>'),
        ('                      <span class="current-price me-3" id="price-container" style="display:none;"></span>',
         '                      <span class="current-price me-3" id="price-container" style="display:none;"></span>\n                      <small id="variant-price-per-m2" class="text-muted me-3" aria-live="polite" hidden></small>'),
        ('<div class="d-flex align-items-center me-3">\n                      <div id="price-loading-container"',
         '<div class="d-flex align-items-center flex-wrap me-3">\n                      <div id="price-loading-container"'),
    ]
    for old, new in changes:
        detail = replace_once(detail, old, new)
    dest = output / 'shop/templates/shop/product/detail.html'
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(detail)
    paths.append('shop/templates/shop/product/detail.html')

    # These dependencies are unchanged production source. Retain them for a
    # complete staging projection and hash checks; do not overwrite them in prod.
    support = ['shop/translation.py', 'shop/product_schema.py']
    for name in support:
        dest = output / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(BASELINE / name, dest)
    hashes = {name: hashlib.sha256((output / name).read_bytes()).hexdigest() for name in paths + support}
    manifest = {
        'release_files': paths,
        'staging_support_files': support,
        'sha256': hashes,
        'expected_production_sha256': {
            'shop/models.py': '265a91a39665b75e1b28079f70a6cbf3acbe10ba0ff56685b2fb7daf4efbc7ad',
            'shop/admin.py': 'b8825ce86e1895fc59afaaecc5b22a319ad46b73d3de9849d71884fae1c1628b',
            **{name: hashlib.sha256((BASELINE / name).read_bytes()).hexdigest() for name in ['shop/views.py', 'shop/templates/shop/product/detail.html'] + support},
        },
    }
    (output / 'manual-material-release.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = build(args.output)
    print('Built', len(result['release_files']), 'release files; no database operation.')
