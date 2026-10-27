"""Manual material information shared by a product's existing package size."""
from collections import defaultdict

from .models import PackageMaterialInfo, Variant


def package_sizes(product):
    if not product or not product.pk:
        return []
    return sorted(size for size in product.variants.exclude(size=None).exclude(size='')
                  .order_by().values_list('size', flat=True).distinct() if size.strip())


def package_material_payload(product_id, size):
    values = None
    if size and size.strip():
        values = PackageMaterialInfo.objects.filter(product_id=product_id, size=size).values(
            'price_per_m2', 'coverage_m2',
        ).first()
    values = values or {'price_per_m2': None, 'coverage_m2': None}
    price = values['price_per_m2']
    return {'price_per_m2': str(price) if price is not None else None,
            'coverage_m2': values['coverage_m2']}


def legacy_material_conflicts(product_id):
    """Read preserved colour values; never choose or overwrite a conflicting value."""
    grouped = defaultdict(lambda: {'price_per_m2': set(), 'coverage_m2': set()})
    rows = Variant.objects.filter(product_id=product_id).exclude(size=None).exclude(size='')
    for size, price, coverage in rows.order_by().values_list(
        'size', 'price_per_m2', 'coverage_m2',
    ).distinct():
        if price is not None:
            grouped[size]['price_per_m2'].add(price)
        if coverage and coverage.strip():
            grouped[size]['coverage_m2'].add(coverage.strip())
    return {size: {field: sorted(values) for field, values in fields.items() if len(values) > 1}
            for size, fields in grouped.items() if any(len(v) > 1 for v in fields.values())}
