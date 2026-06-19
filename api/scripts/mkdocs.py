#!/usr/bin/env python3

import argparse
import importlib
import json
import sys
from pathlib import Path
from typing import Any

from shared.http import HttpResolver

REPO_ROOT = Path(__file__).resolve().parents[1]
BASE_DIRS = {
    "service": REPO_ROOT / "services",
    "worker": REPO_ROOT / "workers",
}
OUTPUT_DIRS = {
    "service": REPO_ROOT / "cdk.out" / "services",
    "worker": REPO_ROOT / "cdk.out" / "workers",
}


def handler_path(kind: str, name: str) -> Path:
    return BASE_DIRS[kind] / name / "src" / name / "handler.py"


def discover(kind: str) -> list[str]:
    base_dir = BASE_DIRS[kind]
    if not base_dir.exists():
        return []

    return sorted(
        path.name
        for path in base_dir.iterdir()
        if path.is_dir() and handler_path(kind, path.name).exists()
    )


def import_app(kind: str, name: str) -> Any:
    src_dir = BASE_DIRS[kind] / name / "src"
    path = handler_path(kind, name)
    if not path.exists():
        raise FileNotFoundError(f"Missing handler: {path}")

    src_dir_str = str(src_dir)
    if src_dir_str not in sys.path:
        sys.path.insert(0, src_dir_str)

    module = importlib.import_module(f"{name}.handler")
    app = getattr(module, "app", None)

    if kind == "service":
        if not isinstance(app, HttpResolver):
            raise TypeError(
                f"{name}.handler.app must be HttpResolver; got {type(app).__name__}"
            )
    elif app is None or not hasattr(app, "manifest"):
        raise TypeError(
            f"{name}.handler.app must provide manifest(); got {type(app).__name__}"
        )

    return app


def build_manifest(kind: str, name: str) -> dict[str, Any]:
    return {kind: name, **import_app(kind, name).manifest()}


def write_manifest(kind: str, name: str, manifest: dict[str, Any]) -> Path:
    output_dir = OUTPUT_DIRS[kind]
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{name}.json"
    output_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate manifests for services and workers."
    )
    parser.add_argument(
        "--service",
        action="append",
        default=[],
        help="Generate only the named service. Can be passed multiple times.",
    )
    parser.add_argument(
        "--worker",
        action="append",
        default=[],
        help="Generate only the named worker. Can be passed multiple times.",
    )
    parser.add_argument(
        "--list-services",
        action="store_true",
        help="List discoverable services and exit.",
    )
    parser.add_argument(
        "--list-workers",
        action="store_true",
        help="List discoverable workers and exit.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.list_services:
        print(*discover("service"), sep="\n")
        return 0

    if args.list_workers:
        print(*discover("worker"), sep="\n")
        return 0

    targets = {
        "service": sorted(set(args.service or discover("service"))),
        "worker": sorted(set(args.worker or discover("worker"))),
    }

    if not any(targets.values()):
        print("No services or workers found.", file=sys.stderr)
        return 1

    failures = 0

    for kind, names in targets.items():
        for name in names:
            try:
                output_path = write_manifest(kind, name, build_manifest(kind, name))
            except Exception as exc:
                failures += 1
                print(f"failed {name}: {exc}", file=sys.stderr)
            else:
                print(f"wrote {output_path}")

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
