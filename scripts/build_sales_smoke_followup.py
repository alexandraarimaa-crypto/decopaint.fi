"""Build the one-file delivery-copy correction found during production smoke."""
import argparse
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.build_sales_flow_release import build as build_full_release
NAME = "shop/templatetags/sales_flow_tags.py"
EXPECTED = "344cdf45c1d4b63b935b902750c2e8b2f8dda3dd62e5bfbeb5ca0bcfa2501755"


def build(output):
    output = Path(output)
    names = [NAME, "cart/templates/cart/checkout.html"]
    with TemporaryDirectory() as temporary:
        build_full_release(temporary)
        for name in names:
            target = output / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((Path(temporary) / name).read_bytes())
    manifest = {"release_files": names, "expected_production_sha256": {NAME: EXPECTED, names[1]: "748a7f03ed82f409029510d2c4f21e4153227faa39469c382d2a8ceb906c5a5f"}, "sha256": {name: hashlib.sha256((output / name).read_bytes()).hexdigest() for name in names}}
    (output / "sales-flow-release.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    build(args.output)
    print("Built two guarded delivery-copy files; no database operation.")
