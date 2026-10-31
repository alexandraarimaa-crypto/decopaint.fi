"""Build the scoped Merchant task release without replacing the live API adapter."""

import argparse
import ast
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
BASELINE = ROOT / 'deployments/merchant-stock-price-20261031/baseline'
RUNTIME_FILES = ('google_shopping/tasks.py',)
EXPECTED_PRODUCTION = {
    'google_shopping/tasks.py': 'f0ff1a4a7dbfa008cf6f446822b9b27d29e1318d026614c7cacc7a4115dae897',
    'google_shopping/api.py': '2ce7fa2ec9405e18494993fd531663af89d3d537679059c3d2741c35e9873298',
    'google_shopping/merchant_payload.py': 'b7100c56fb4b3dff63f4f4741ced3cb61d12a354d019f5ccec412026290e97a2',
}


def build(output):
    for name, expected in EXPECTED_PRODUCTION.items():
        baseline = (BASELINE / name).read_bytes()
        if hashlib.sha256(baseline).hexdigest() != expected:
            raise ValueError(f'Audited baseline changed: {name}')
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    installed = {}
    for name in RUNTIME_FILES:
        data = (ROOT / name).read_bytes()
        ast.parse(data)
        destination = output / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        installed[name] = hashlib.sha256(data).hexdigest()
    manifest = {
        'runtime_sha256': installed,
        'expected_production_sha256': EXPECTED_PRODUCTION,
        'preserved_support_files': [
            name for name in EXPECTED_PRODUCTION if name not in RUNTIME_FILES
        ],
        'database_migrations': [],
        'external_updates': 'Separate existing-offer-only refresh after code verification.',
    }
    (output / 'merchant-stock-release.json').write_text(
        json.dumps(manifest, indent=2) + '\n'
    )
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    arguments = parser.parse_args()
    print(json.dumps(build(arguments.output), indent=2))
