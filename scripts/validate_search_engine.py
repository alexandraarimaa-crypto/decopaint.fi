#!/usr/bin/env python3
"""Validate the source-grounded search artifact without a production DB."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from types import SimpleNamespace


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from shop.search_engine import load_search_index, rank_products  # noqa: E402


EXPECTED_PREFIXES = {
    "puulattian lakka": ["ecoprotettivo-parquet"],
    "siloksaanimaali ulkoseinä": ["duaflex", "silkos-torino"],
    "nikotiinitahrat": ["decortina-new"],
    "PVC pohjamaali": [
        "aggrappante-ecologico",
        "250-biofissativo-alta-adesione",
        "flexigrap-liscio",
        "flexigrap",
    ],
    "homeenpoisto sisäseinä": ["sterylfix"],
    "betonin vedenhylkivyys": ["betoncryll-idrorepellente"],
    "marmoriino": [
        "marmorino-naturale",
        "marmorino-naturale-fine",
        "protettivo-per-stucco-e-marmorino",
    ],
    "patterimaali": ["ecosmalto-thermo"],
    "ruosteenmuuntoaine": ["convertitore-ecologico"],
}


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", required=True, type=Path)
    parser.add_argument("--overrides", required=True, type=Path)
    parser.add_argument("--expected-count", type=int, default=154)
    return parser.parse_args()


def fail(message):
    raise AssertionError(message)


def main():
    args = parse_args()
    records = json.loads(args.index.read_text(encoding="utf-8"))
    if len(records) != args.expected_count:
        fail(f"Expected {args.expected_count} records, found {len(records)}")

    slugs = [record.get("slug") for record in records]
    if len(set(slugs)) != len(slugs) or any(not slug for slug in slugs):
        fail("Product slugs must be present and unique")

    load_search_index.cache_clear()
    index = load_search_index(str(args.index), str(args.overrides))
    if len(index) != args.expected_count:
        fail(f"Loaded index contains {len(index)} unique products")

    products = [
        SimpleNamespace(
            name=record["product"],
            slug=record["slug"],
            available=True,
            attributes=[],
        )
        for record in records
    ]

    checked = {}
    for query, expected in EXPECTED_PREFIXES.items():
        actual = [product.slug for product in rank_products(products, query, index)]
        if actual[: len(expected)] != expected:
            fail(f"{query!r}: expected prefix {expected!r}, got {actual!r}")
        checked[query] = actual

    if "antiruggine-ecologico" in checked["PVC pohjamaali"]:
        fail("Antiruggine must not inherit PVC compatibility from mislinked PDFs")

    hidden = SimpleNamespace(
        name="Patterimaali Ecosmalto Thermo",
        slug="ecosmalto-thermo",
        available=False,
        attributes=[],
    )
    if rank_products([hidden], "patterimaali", index):
        fail("Unavailable products must never be returned")

    print(
        json.dumps(
            {
                "status": "ok",
                "products": len(index),
                "golden_queries": len(checked),
                "unavailable_products_excluded": True,
                "mislinked_pdf_terms_excluded": True,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
