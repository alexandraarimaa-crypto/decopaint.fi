"""Guarded, reversible correction of three descriptive records; no sale-price writes."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys


def snapshot():
    from shop.models import Attribute, PackageMaterialInfo, Product, Variant
    product = Product.objects.get(pk=1311, slug="marmorino-naturale-fine")
    attribute_fields = ["id", "product_id", "sufficiency", "sufficiency_fi", "sufficiency_sv", "sufficiency_en"]
    return {
        "attribute": Attribute.objects.values(*attribute_fields).get(pk=728, product=product),
        "packages": list(PackageMaterialInfo.objects.filter(pk__in=[40, 41], product=product).order_by("pk").values("id", "product_id", "size", "coverage_m2", "price_per_m2")),
        "variant_fingerprint": hashlib.sha256(json.dumps(list(Variant.objects.filter(product=product).order_by("pk").values()), default=str, sort_keys=True).encode()).hexdigest(),
    }


def corrected(before):
    after = json.loads(json.dumps(before, default=str))
    attribute = after["attribute"]
    for field in ["sufficiency", "sufficiency_fi", "sufficiency_sv"]:
        if attribute[field].replace(" ", "") != "0,5-0,75kg/m2":
            raise ValueError("Consumption changed since audit; stop for review")
    if attribute["sufficiency_en"].replace(" ", "") != "0.5-0.75kg/m2":
        raise ValueError("English consumption changed since audit")
    attribute.update(sufficiency="1–1,5 kg/m² / 2 kerrosta", sufficiency_fi="1–1,5 kg/m² / 2 kerrosta", sufficiency_sv="1–1,5 kg/m² / 2 lager totalt", sufficiency_en="1–1.5 kg/m² / 2 coats total")
    if len(after["packages"]) != 2:
        raise ValueError("Expected exactly two audited package rows")
    for row in after["packages"]:
        expected = {40: ("5 kg", "10-15", "4.93", "3,3–5", "9.86"), 41: ("20 kg", "40-60", "4.46", "13,3–20", "8.93")}[row["id"]]
        if (row["size"], row["coverage_m2"], row["price_per_m2"]) != expected[:3]:
            raise ValueError("Package information changed since audit")
        row.update(coverage_m2=expected[3], price_per_m2=expected[4])
    return after


def write_descriptions(state):
    from shop.models import Attribute, PackageMaterialInfo
    attribute = state["attribute"]
    Attribute.objects.filter(pk=attribute["id"], product_id=1311).update(**{
        key: value for key, value in attribute.items() if key.startswith("sufficiency")
    })
    for row in state["packages"]:
        PackageMaterialInfo.objects.filter(pk=row["id"], product_id=1311, size=row["size"]).update(
            coverage_m2=row["coverage_m2"], price_per_m2=row["price_per_m2"],
        )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True, type=Path)
    parser.add_argument("--backup", required=True, type=Path)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--restore", action="store_true")
    args = parser.parse_args()
    sys.path.insert(0, str(args.project.resolve()))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    import django
    django.setup()
    before = json.loads(json.dumps(snapshot(), default=str))
    if args.restore:
        backup = json.loads(args.backup.read_text())
        if before != backup["after"]:
            raise ValueError("Current records differ from this release; refusing to overwrite")
        write_descriptions(backup["before"])
        assert json.loads(json.dumps(snapshot(), default=str)) == backup["before"]
        print("Restored three descriptive rows; variant fingerprint unchanged.")
        return
    after = corrected(before)
    if not args.apply:
        print("Validated three descriptive rows; dry run, no writes.")
        return
    # Exclusive mode prevents accidentally overwriting an earlier rollback copy.
    descriptor = os.open(args.backup, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w") as stream:
        json.dump({"before": before, "after": after}, stream, ensure_ascii=False, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
    assert json.loads(args.backup.read_text())["before"] == before
    try:
        write_descriptions(after)
        assert json.loads(json.dumps(snapshot(), default=str)) == after
    except Exception:
        write_descriptions(before)
        raise
    print("Corrected three descriptive rows; all variant fields unchanged. Verified rollback backup.")


if __name__ == "__main__":
    main()
