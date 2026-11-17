"""Build only the contact-order correction after the first relocation release."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.build_relocation_release import build as build_full

NAME = "shop/templates/shop/else/contact.html"
EXPECTED = "cc1eb194eed05129210bff1c4d6d2dbaa698f4db50bcf39bcc42e43921c1d84b"


def build(output):
    output = Path(output)
    with TemporaryDirectory() as temporary:
        build_full(temporary)
        data = (Path(temporary) / NAME).read_bytes()
    target = output / NAME
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    manifest = {"release_files": [NAME], "expected_production_sha256": {NAME: EXPECTED}, "sha256": {NAME: hashlib.sha256(data).hexdigest()}}
    (output / "sales-flow-release.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    build(parser.parse_args().output)
    print("Built one guarded contact-layout file; no database operation.")
