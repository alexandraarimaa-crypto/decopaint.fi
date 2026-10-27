from django.db import migrations


def copy_unambiguous_values(apps, schema_editor):
    Variant = apps.get_model('shop', 'Variant')
    Package = apps.get_model('shop', 'PackageMaterialInfo')
    alias = schema_editor.connection.alias
    grouped = {}
    rows = Variant.objects.using(alias).exclude(product_id=None).exclude(size=None).exclude(size='')
    for product_id, size, price, coverage in rows.order_by().values_list(
        'product_id', 'size', 'price_per_m2', 'coverage_m2',
    ).distinct().iterator():
        if not size.strip():
            continue
        fields = grouped.setdefault((product_id, size), {'price': set(), 'coverage': set()})
        if price is not None:
            fields['price'].add(price)
        if coverage and coverage.strip():
            fields['coverage'].add(coverage.strip())

    for (product_id, size), fields in grouped.items():
        # Empty values do not contradict a single manually entered value.
        # Conflicting fields remain empty until explicitly reviewed in Tuotteet.
        Package.objects.using(alias).get_or_create(
            product_id=product_id, size=size,
            defaults={
                'price_per_m2': next(iter(fields['price'])) if len(fields['price']) == 1 else None,
                'coverage_m2': next(iter(fields['coverage'])) if len(fields['coverage']) == 1 else None,
            },
        )
    # Legacy columns and every original value are deliberately retained.


class Migration(migrations.Migration):
    dependencies = [('shop', '0062_packagematerialinfo')]
    operations = [migrations.RunPython(copy_unambiguous_values, migrations.RunPython.noop)]
