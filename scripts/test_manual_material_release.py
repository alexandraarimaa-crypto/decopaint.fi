"""Check the generated production-compatible projection using synthetic data."""
import ast
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from build_manual_material_release import BASELINE, ROOT, build


def parsed_functions(source):
    return {node.name: node for node in ast.parse(source).body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}


with tempfile.TemporaryDirectory(prefix='manual-material-runtime-') as temporary:
    project = Path(temporary) / 'project'
    project.mkdir()
    for name in (
        'config', 'shop', 'users', 'cart', 'order', 'google_shopping',
        'pk_paytrail', 'pk_postnord', 'mail', 'blog', 'b2b', 'services', 'courses',
    ):
        shutil.copytree(ROOT / name, project / name, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    shutil.copyfile(ROOT / 'manage.py', project / 'manage.py')
    manifest = build(project)

    original = parsed_functions((BASELINE / 'shop/views.py').read_text())
    generated = parsed_functions((project / 'shop/views.py').read_text())
    assert original.keys() == generated.keys(), 'Runtime view functions were added/removed'
    price = generated['get_variant_price']
    removed = []
    for node in ast.walk(price):
        if isinstance(node, ast.Dict):
            pairs = []
            for key, value in zip(node.keys, node.values):
                if isinstance(key, ast.Constant) and key.value in ('price_per_m2', 'coverage_m2'):
                    removed.append(key.value)
                else:
                    pairs.append((key, value))
            node.keys = [key for key, _ in pairs]
            node.values = [value for _, value in pairs]
    assert sorted(removed) == ['coverage_m2', 'price_per_m2']
    for name in original:
        assert ast.dump(original[name]) == ast.dump(generated[name]), name + ' changed beyond manual response fields'
    for name in manifest['staging_support_files']:
        assert (project / name).read_bytes() == (BASELINE / name).read_bytes(), name
    assert not (project / 'shop/migrations/0060_variant_material_info.py').exists()
    assert (project / 'shop/migrations/0061_variant_material_info.py').exists()

    env = os.environ.copy()
    env.pop('DJANGO_SETTINGS_MODULE', None)
    subprocess.run([
        sys.executable, 'manage.py', 'test', 'shop.tests_variant_material_info',
        '--settings=config.variant_info_test_settings', '--noinput',
    ], cwd=project, env=env, check=True)
    print('Runtime projection passed: deployed logic preserved; migration chain and admin/API tests passed.')
