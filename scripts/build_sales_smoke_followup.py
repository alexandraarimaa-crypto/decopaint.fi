"""Build the one-file delivery-copy correction found during production smoke."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAME = "shop/templatetags/sales_flow_tags.py"
EXPECTED = "344cdf45c1d4b63b935b902750c2e8b2f8dda3dd62e5bfbeb5ca0bcfa2501755"


def build(output):
    output = Path(output)
    target = output / NAME
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes((ROOT / NAME).read_bytes())
    manifest = {"release_files": [NAME], "expected_production_sha256": {NAME: EXPECTED}, "sha256": {NAME: hashlib.sha256(target.read_bytes()).hexdigest()}}
    (output / "sales-flow-release.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    build(args.output)
    print("Built one guarded delivery-copy file; no database operation.")
