#!/usr/bin/env python3
"""Static validation for the source-grounded Finnish SEO P0 candidate."""

from pathlib import Path
import ast
import sys


ROOT = Path(__file__).resolve().parent.parent


def fail(message):
    print(f"FAIL: {message}")
    return False


def main():
    checks_ok = True
    seo_source = (ROOT / "shop" / "seo.py").read_text(encoding="utf-8")
    seo_tree = ast.parse(seo_source, filename="shop/seo.py")
    constants = {}
    for node in seo_tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id in {
                "HOME_SEO",
                "CATALOG_SEO",
                "CATEGORY_SEO",
                "PRODUCT_SEO",
            }:
                constants[target.id] = ast.literal_eval(node.value)

    records = [constants["HOME_SEO"], constants["CATALOG_SEO"]]
    records.extend(constants["CATEGORY_SEO"].values())
    records.extend(constants["PRODUCT_SEO"].values())
    titles = []
    for record in records:
        title = record["title"]
        description = record["description"]
        if len(title) > 65:
            checks_ok = fail(f"title exceeds 65 characters: {title}")
        if len(description) > 180:
            checks_ok = fail(f"description exceeds 180 characters: {title}")
        titles.append(title)
    if len(titles) != len(set(titles)):
        checks_ok = fail("SEO titles are not unique")
    for forbidden_claim in ("mikrosementti", "märkätilaan"):
        if forbidden_claim in seo_source.lower():
            checks_ok = fail(f"unverified claim in SEO metadata: {forbidden_claim}")

    python_files = [
        ROOT / "shop" / "seo.py",
        ROOT / "shop" / "product_schema.py",
        ROOT / "shop" / "views.py",
        ROOT / "shop" / "sitemaps.py",
        ROOT / "shop" / "urls.py",
        ROOT / "shop" / "tests_seo.py",
    ]
    for path in python_files:
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, SyntaxError) as exc:
            checks_ok = fail(f"Python syntax {path.relative_to(ROOT)}: {exc}")

    base = (ROOT / "shop/templates/shop/base/base.html").read_text(encoding="utf-8")
    required_base_markers = [
        "current_language|default:'fi'",
        'name="description" content="{{ seo.description',
        'name="robots" content="{{ seo_robots',
        "{{ request.path }}",
    ]
    for token in required_base_markers:
        if token not in base:
            checks_ok = fail(f"base template missing {token!r}")

    for block_name in ("open_graph", "schema_markup"):
        if f"{{% block {block_name} %}}" not in base:
            checks_ok = fail(f"base template does not render {block_name}")

    forbidden = {
        'name="keywords"': "obsolete meta keywords",
        'href="{{ request.build_absolute_uri }}"': "query-bearing canonical",
        "mikrosementti": "unverified microcement claim",
    }
    for token, label in forbidden.items():
        if token in base:
            checks_ok = fail(f"base template contains {label}")

    homepage = (ROOT / "shop/templates/shop/else/main.html").read_text(encoding="utf-8")
    for duplicate_tag in (
        "tag_slug='sisustusmaalit'",
        "tag_slug='sisustuslaastit'",
        "tag_slug='koristemaalit'",
        "tag_slug='ulkomaalit'",
    ):
        if duplicate_tag in homepage:
            checks_ok = fail(f"homepage still links to duplicate {duplicate_tag}")

    product = (ROOT / "shop/templates/shop/product/detail.html").read_text(encoding="utf-8")
    required_product_markers = (
        'property="og:type" content="product"',
        'id="product-structured-data"',
        "product_structured_data_json|safe",
    )
    for token in required_product_markers:
        if token not in product:
            checks_ok = fail(f"product template missing {token!r}")
    for token in ('"description": " {{ product.description|safe }}"', '"availability": "https://schema.org/InStock"'):
        if token in product:
            checks_ok = fail(f"unsafe legacy Product markup remains: {token}")

    if not checks_ok:
        return 1
    print("SEO P0 static validation: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
