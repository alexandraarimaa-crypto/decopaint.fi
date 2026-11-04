"""Emit only allowlisted, secret-free source entries for the GitHub connector."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
FILES = [
    ".github/workflows/ci.yml", "shop/measurement_identity.py", "shop/sales_flow.py",
    "shop/tests_measurement_identity.py", "shop/tests_sales_release.py", "shop/tests_sales_flow.py",
    "shop/templatetags/sales_flow_tags.py", "shop/static/assets/js/analytics.js",
    "shop/static/assets/js/analytics-location.js", "shop/static/assets/js/sales-product.js",
    "shop/static/assets/css/sales-flow.css", "shop/templates/shop/product/sales_calculator.html",
    "shop/templates/shop/product/sales_catalogue.html", "scripts/build_sales_flow_release.py",
    "scripts/correct_marmorino_coverage.py", "scripts/test_sales_product.mjs",
    "scripts/test_sales_analytics.mjs", "scripts/export_sales_commit.py",
    "docs/changelog.md", "docs/testing.md", "docs/deployment.md", "docs/rollback.md",
    "docs/sales-flow-2026-11-04.md",
    "scripts/render_sales_preview.py", "scripts/install_sales_release.py",
]
FILES += [str(path.relative_to(ROOT)) for path in sorted((ROOT / "deployments/sales-flow-20261103").rglob("*")) if path.is_file() and "__pycache__" not in path.parts]
if __name__ == "__main__":
    selected = FILES[int(sys.argv[1]):int(sys.argv[2])] if len(sys.argv) > 1 else FILES
    print(json.dumps([{"path": name, "mode": "100644", "type": "blob", "content": (ROOT / name).read_bytes().decode("utf-8")} for name in selected]))
