"""Visible product options shared by the storefront and Merchant synchronization."""

from django.db.models import Min

from .models import Variant


def _unique_visible_values(values):
    result = []
    seen = set()
    for value in values:
        value = (value or "").strip()
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def get_storefront_options(product_id):
    """Return the radio options in their initial, deterministic display order."""
    variants = Variant.objects.filter(product_id=product_id, active=True)
    size_rows = (
        variants.exclude(size__isnull=True)
        .exclude(size="")
        .values("size")
        .annotate(min_price=Min("price"))
        .order_by("min_price", "size")
    )
    options = {"sizes": _unique_visible_values(row["size"] for row in size_rows)}
    for field, key in (("base", "bases"), ("grain", "grains"), ("gloss", "glosses")):
        visible = variants.exclude(**{f"{field}__isnull": True}).exclude(**{field: ""})
        if field == "base":
            visible = visible.exclude(base__icontains="base")
        # Explicit ordering avoids backend-dependent DISTINCT ordering. The
        # same list is used by the radio controls and the Merchant selector.
        options[key] = _unique_visible_values(
            visible.order_by("id").values_list(field, flat=True)
        )
    return options
