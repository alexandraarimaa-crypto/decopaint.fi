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

# Manifest of the audited deployed 7e7b662 runtime before the package correction.
CURRENT_PRODUCTION_SHA256 = {'shop/models.py': '7c646dbde0bd906eb75cfde1c0379e14e8b6d4a65f440f0c15102b9a3d7f6dca',
 'shop/admin.py': '51e8d4693439751a1a6e271d53633c0cbdac6863936e0187aa20d09792e4f734',
 'shop/migrations/0060_attribute_a_class_en_attribute_a_class_fi_and_more.py': '0e80dcf77e38086a80cd54c1f16198d7ec32626c0af5c217cffb46f5e0e376e8',
 'shop/migrations/0061_variant_material_info.py': 'cd805c5fcc273bb368476e8f32b9658ab16482968d3f12a1d379a14472a23361',
 'shop/static/assets/js/variant-material-info.js': 'cfdd3759d6d489f753755ca555629d46ec0ca3b35f5c5354d67801f44cddad19',
 'shop/templates/admin/shop/variant_material_info.html': '049979a781b4776fec6e2dc356878dc239af27f00853519ebc622e5793997a92',
 'shop/templates/admin/shop/headerless_variant_material_info.html': 'cd2eb8277e133212f1b290c22c2cc01d7e6e43bf16fd568d842864a50918630f',
 'shop/templatetags/variant_material_info_tags.py': 'b090bb405a1bd8139296a3d86cdbd3fa77a5468ef86ccc57165f25f2a07c2131',
 'shop/views.py': '8895d8a79de1436f9f52168735238cf18671443ecb73340835a81538e1bad5aa',
 'shop/templates/shop/product/detail.html': 'f0c5c02fec8484a47a1e773f91c9c7b92d500e85f33dd49c15cca459edaa64a1',
 'shop/translation.py': 'fd77ea5f7cb5bad9655033065f09867a3104977388b1cf5679854952f9f7ce2a',
 'shop/product_schema.py': 'e3f415d88a0be2b89a0b327fd47078a252f900a28b8a1da8614e838656ed77fc'}


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
        'shop/migrations/0062_packagematerialinfo.py',
        'shop/migrations/0063_copy_unambiguous_package_material_info.py',
        'shop/material_info.py',
        'shop/static/assets/js/variant-material-info.js',
        'shop/templates/admin/shop/variant_material_info.html',
        'shop/templates/admin/shop/headerless_variant_material_info.html',
        'shop/templatetags/variant_material_info_tags.py',
    ]
    for name in paths:
        dest = output / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, dest)

    views = 'from .material_info import package_material_payload\n' + (BASELINE / 'shop/views.py').read_text()
    views = replace_once(
        views, "                'is_asiakas_group': is_asiakas_group\n",
        "                'is_asiakas_group': is_asiakas_group,\n"
        "                **package_material_payload(product.pk, variant.size),\n",
    )
    (output / 'shop/views.py').write_text(views)
    paths.append('shop/views.py')

    detail = (BASELINE / 'shop/templates/shop/product/detail.html').read_text()
    changes = [
        ('    <script>\n    $(document).ready(function () {\n        // Global price management variables',
         '    <script src="{% static \'assets/js/variant-material-info.js\' %}?v=20261027-packages"></script>\n    <script>\n    $(document).ready(function () {\n        // Global price management variables'),
        ("        function showPriceLoading() {\n            $('#price-container').hide();",
         "        function showPriceLoading() {\n            window.prepareVariantMaterialInfo($(\'input[name=size]:checked\').val());\n            $('#price-container').hide();"),
        ('        function updatePrice() {\n            if (priceLoading) {',
         '        function updatePrice() {\n            window.prepareVariantMaterialInfo($(\'input[name=size]:checked\').val());\n            if (priceLoading) {'),
        ('                    if (data.price !== undefined) {\n                        var unit_price',
         '                    if (data.price !== undefined) {\n                        if (!pendingPriceUpdate) {\n                            window.updateVariantMaterialInfo(data);\n                        }\n                        var unit_price'),
        ('            <span class="fw-semibold text-body-emphasis me-7">{% translate "Koko:" %} </span>',
         '            <div class="d-flex align-items-baseline flex-wrap gap-2">\n              <span class="fw-semibold text-body-emphasis me-7">{% translate "Koko:" %} </span>\n              <small id="variant-coverage" class="text-body-emphasis" aria-live="polite" hidden></small>\n            </div>'),
        ('                      <span class="current-price me-3" id="price-container" style="display:none;"></span>',
         '                      <span class="current-price me-3" id="price-container" style="display:none;"></span>\n                      <small id="variant-price-per-m2" class="text-body-emphasis me-3" aria-live="polite" hidden></small>'),
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
        'expected_production_sha256': CURRENT_PRODUCTION_SHA256.copy(),
    }
    (output / 'manual-material-release.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = build(args.output)
    print('Built', len(result['release_files']), 'release files; no database operation.')
