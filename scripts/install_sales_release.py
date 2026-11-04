"""Verify and install only an audited release's allowlisted files, with rollback."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def atomic_write(path, data, mode=0o644):
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".sales-release-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--backup", type=Path, required=True)
    parser.add_argument("--static-root", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--restore", action="store_true")
    args = parser.parse_args()
    manifest = json.loads((args.candidate / "sales-flow-release.json").read_text())
    if args.restore:
        records = json.loads((args.backup / "files.json").read_text())
        for record in records:
            if digest(Path(record["target"])) != record["installed"]:
                raise ValueError("Later edits exist; refuse to overwrite " + record["name"])
        for record in records:
            target = Path(record["target"])
            if record["before"] is None:
                target.unlink()
            else:
                source = args.backup / record["copy"]
                assert digest(source) == record["before"]
                atomic_write(target, source.read_bytes())
        print("Restored only this release's files and static assets.")
        return
    targets = []
    for name in manifest["release_files"]:
        if name.startswith("/") or ".." in Path(name).parts:
            raise ValueError("Unsafe release path")
        source = args.candidate / name
        assert digest(source) == manifest["sha256"][name], name
        if name.endswith(".py"):
            compile(source.read_text(), name, "exec")
        target = args.project / name
        expected = manifest["expected_production_sha256"][name]
        if digest(target) != expected:
            raise ValueError("Production source drift: " + name)
        targets.append((name, source, target, expected))
        if name.startswith("shop/static/"):
            static_target = args.static_root / name[len("shop/static/"):]
            if static_target.resolve() != target.resolve():
                targets.append(("published/" + name, source, static_target, digest(static_target)))
    if not args.apply:
        print("Validated", len(targets), "source/static targets; dry run, no writes.")
        return
    args.backup.mkdir(mode=0o700, parents=False, exist_ok=False)
    records = []
    for index, (name, source, target, expected) in enumerate(targets):
        record = {"name": name, "target": str(target), "before": expected, "installed": digest(source), "copy": str(index)}
        if expected:
            atomic_write(args.backup / str(index), target.read_bytes(), 0o600)
            assert digest(args.backup / str(index)) == expected
        records.append(record)
    atomic_write(args.backup / "files.json", (json.dumps(records, indent=2) + "\n").encode(), 0o600)
    # Install dependencies/assets first; importing views and base template last.
    targets.sort(key=lambda entry: (entry[0].endswith("base/base.html"), entry[0].endswith("views.py"), entry[0]))
    for name, source, target, expected in targets:
        if digest(target) != expected:
            raise ValueError("Source changed after backup: " + name)
        atomic_write(target, source.read_bytes())
        assert digest(target) == digest(source)
    print("Installed and verified", len(targets), "targets; private backups verified. Restart existing application separately.")


if __name__ == "__main__":
    main()
