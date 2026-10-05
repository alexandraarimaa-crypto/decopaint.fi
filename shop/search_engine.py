"""Source-grounded product search for Finnish customer queries.

The engine intentionally searches a controlled product index instead of raw
HTML descriptions. Technical terms must come from the product card or its
linked technical data sheet. The module is standard-library only so the
ranking rules can be tested without a Django database.
"""

from __future__ import annotations

import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path


FIELD_WEIGHTS = {
    "name": 100,
    "controlled_misspelling": 85,
    "product_type": 65,
    "purpose": 58,
    "surface": 52,
    "scope": 42,
    "method": 24,
    "brand": 18,
}

# Each input token expands to one or more required technical concepts. This is
# deliberately a small allowlist: unrestricted fuzzy matching could turn a
# limitation or a tool mention into a false compatibility result.
TOKEN_EXPANSIONS = {
    "puulattia": (("puu",), ("lattia",)),
    "puulattian": (("puu",), ("lattia",)),
    "lattialakka": (("lattia",), ("lakka",)),
    "ulkoseina": (("ulko",), ("seina",)),
    "ulkoseinat": (("ulko",), ("seina",)),
    "sisaseina": (("sisa",), ("seina",)),
    "sisaseinat": (("sisa",), ("seina",)),
    "betonin": (("betoni",),),
    "betonille": (("betoni",),),
    "marmoriino": (("marmorino",),),
    "marmorinoo": (("marmorino",),),
    "siloxaanimaali": (("siloksaanimaali",),),
    "siloksanimaali": (("siloksaanimaali",),),
    "nikotiinitahrat": (("nikotiini",),),
    "nikotiinitahra": (("nikotiini",),),
    "homeenpoistoaine": (("homeenpoisto",),),
    "homeenestomaali": (("homeenesto",),),
    "ruosteenmuuntoaine": (("ruosteenmuunto",),),
    "ruosteenestoaine": (("ruosteenesto",),),
}

PROTECTION_TERMS = {"suoja", "suojalakka", "suoja-aine", "lakka"}


def normalize_text(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or "").casefold())
    text = "".join(char for char in text if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def _stable_unique(values):
    seen = set()
    result = []
    for value in values:
        normalized = normalize_text(value)
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return result


def query_groups(query: str) -> list[tuple[str, ...]]:
    groups = []
    for token in normalize_text(query).split():
        expansion = TOKEN_EXPANSIONS.get(token)
        if expansion:
            groups.extend(expansion)
            continue

        alternatives = [token]
        # Conservative Finnish case-form support. The original token remains
        # an alternative, so short names and brand names are never truncated.
        if len(token) >= 6 and token.endswith("n"):
            alternatives.append(token[:-1])
        groups.append(tuple(_stable_unique(alternatives)))
    return groups


def _field_values(record: dict) -> dict[str, list[str]]:
    keywords = record.get("keywords") or {}
    filters = record.get("technical_filters") or {}
    return {
        "name": _stable_unique(
            [record.get("product", ""), *(keywords.get("exact_and_name_variants") or [])]
        ),
        "controlled_misspelling": _stable_unique(
            keywords.get("controlled_misspellings") or []
        ),
        "brand": _stable_unique(keywords.get("brands") or []),
        "product_type": _stable_unique(keywords.get("product_types") or []),
        "purpose": _stable_unique(
            [
                *(keywords.get("purposes") or []),
                *(filters.get("purposes") or []),
            ]
        ),
        "surface": _stable_unique(
            [
                *(keywords.get("surfaces") or []),
                *(filters.get("compatible_surfaces") or []),
            ]
        ),
        "scope": _stable_unique(
            [*(keywords.get("scope") or []), *(filters.get("scope") or [])]
        ),
        "method": _stable_unique(
            [
                *(keywords.get("methods") or []),
                *(filters.get("application_methods") or []),
            ]
        ),
    }


def _merge_override(record: dict, override: dict) -> dict:
    if not override:
        return record
    merged = json.loads(json.dumps(record))
    filters = merged.setdefault("technical_filters", {})
    keyword_map = {
        "purposes": "purposes",
        "surfaces": "compatible_surfaces",
        "scope": "scope",
        "methods": "application_methods",
    }
    for source_key, target_key in keyword_map.items():
        removed = {
            normalize_text(value)
            for value in override.get(f"remove_{source_key}", [])
            if normalize_text(value)
        }
        if removed:
            filters[target_key] = [
                value
                for value in filters.get(target_key, [])
                if normalize_text(value) not in removed
            ]
            keywords = merged.setdefault("keywords", {})
            keywords[source_key] = [
                value
                for value in keywords.get(source_key, [])
                if normalize_text(value) not in removed
            ]
        if override.get(source_key):
            filters[target_key] = _stable_unique(
                [*(filters.get(target_key) or []), *override[source_key]]
            )
    if override.get("system_role"):
        merged["system_role"] = override["system_role"]
    if override.get("source"):
        merged.setdefault("search_override_source", override["source"])
    return merged


@lru_cache(maxsize=8)
def load_search_index(index_path: str, overrides_path: str = "") -> dict[str, dict]:
    path = Path(index_path)
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    overrides = {}
    if overrides_path and Path(overrides_path).is_file():
        raw_overrides = json.loads(Path(overrides_path).read_text(encoding="utf-8"))
        overrides = raw_overrides.get("products", raw_overrides)

    result = {}
    for record in payload:
        slug = normalize_text(record.get("slug", "")).replace(" ", "-")
        if not slug:
            continue
        result[slug] = _merge_override(record, overrides.get(slug, {}))
    return result


def _fallback_record(product) -> dict:
    attributes = getattr(product, "attributes", [])
    if hasattr(attributes, "all"):
        attributes = attributes.all()
    families = []
    purposes = []
    applications = []
    for attribute in attributes or []:
        families.append(getattr(attribute, "family", ""))
        purposes.append(getattr(attribute, "purpose", ""))
        applications.append(getattr(attribute, "application", ""))
    return {
        "product": getattr(product, "name", ""),
        "slug": getattr(product, "slug", ""),
        "keywords": {
            "exact_and_name_variants": [getattr(product, "name", ""), *families],
            "purposes": purposes,
            "surfaces": applications,
        },
        "technical_filters": {},
    }


def _term_matches(term: str, value: str) -> bool:
    if term == value:
        return True
    value_tokens = value.split()
    if term in value_tokens:
        return True
    # Finnish compounds such as tartuntapohjamaali and parkettilakka need
    # controlled substring matching. Very short fragments are never accepted.
    return len(term) >= 4 and any(term in token for token in value_tokens)


def _score_record(record: dict, query: str, groups: list[tuple[str, ...]]) -> int | None:
    fields = _field_values(record)
    normalized_query = normalize_text(query)
    score = 0

    if normalized_query in fields["name"]:
        score += 260
    elif any(normalized_query in value for value in fields["name"]):
        score += 90

    for alternatives in groups:
        best = 0
        for field_name, values in fields.items():
            if any(
                _term_matches(term, value)
                for term in alternatives
                for value in values
            ):
                best = max(best, FIELD_WEIGHTS[field_name])
        if not best:
            return None
        score += best

    if record.get("system_role") == "companion":
        query_tokens = set(normalized_query.split())
        if not query_tokens.intersection(PROTECTION_TERMS):
            score -= 70
    return score


def rank_products(products, query: str, index: dict[str, dict]):
    """Return available products ordered by technical relevance."""
    groups = query_groups(query)
    if not groups:
        return []

    ranked = []
    for product in products:
        if not getattr(product, "available", True):
            continue
        slug = normalize_text(getattr(product, "slug", "")).replace(" ", "-")
        record = index.get(slug) or _fallback_record(product)
        score = _score_record(record, query, groups)
        if score is None:
            continue
        product.search_score = score
        product.search_system_role = record.get("system_role", "primary")
        ranked.append(product)

    ranked.sort(
        key=lambda product: (
            -product.search_score,
            normalize_text(getattr(product, "name", "")),
        )
    )
    return ranked
