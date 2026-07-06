#!/usr/bin/env python3

import argparse
import importlib
import json
import sys
import traceback
from pathlib import Path
from typing import Any, Protocol

REPO_ROOT = Path(__file__).resolve().parents[1]


class ManifestApp(Protocol):
    def manifest(self) -> dict[str, Any]: ...


def collect_handlers(kind: str) -> dict[str, tuple[Path, Path]]:
    base_dir = REPO_ROOT / kind
    if not base_dir.exists():
        return {}

    handlers: dict[str, tuple[Path, Path]] = {}
    for project_dir in sorted(p for p in base_dir.iterdir() if p.is_dir()):
        src_dir = project_dir / "src"
        if not src_dir.exists():
            continue

        for path in sorted(src_dir.glob("**/handler.py")):
            name = ".".join(path.parent.relative_to(src_dir).parts)
            if name in handlers and handlers[name][0] != path:
                raise RuntimeError(
                    f"Ambiguous handler for {name}: {handlers[name][0]}, {path}"
                )
            handlers[name] = (path, src_dir)

    return handlers


def discover(kind: str) -> list[str]:
    return sorted(collect_handlers(kind))


def import_app(kind: str, name: str) -> ManifestApp:
    try:
        _, src_dir = collect_handlers(kind)[name]
    except KeyError as exc:
        raise FileNotFoundError(f"Missing handler for {kind}.{name}") from exc

    if (src := str(src_dir)) not in sys.path:
        sys.path.insert(0, src)

    module = importlib.import_module(f"{name}.handler")
    app = getattr(module, "app", None)
    if not callable(getattr(app, "manifest", None)):
        raise TypeError(f"{name}.handler.app must provide manifest(); got {type(app)}")
    return app  # type: ignore


def write_manifest(kind: str, name: str, manifest: dict[str, Any]) -> Path:
    output_dir = REPO_ROOT / "cdk.out" / kind
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{name}.json"
    output_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return output_path


def clear_manifests(kind: str) -> None:
    output_dir = REPO_ROOT / "cdk.out" / kind
    if output_dir.exists():
        for path in output_dir.glob("*.json"):
            path.unlink()


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
        print(*discover("services"), sep="\n")
        return 0
    if args.list_workers:
        print(*discover("workers"), sep="\n")
        return 0

    targets = {
        "services": sorted(set(args.service or discover("services"))),
        "workers": sorted(set(args.worker or discover("workers"))),
    }
    if not any(targets.values()):
        print("No services or workers found.", file=sys.stderr)
        return 1

    for kind, names in targets.items():
        if names:
            clear_manifests(kind)

    failures = 0
    for kind, names in targets.items():
        for name in names:
            try:
                manifest = {kind: name, **import_app(kind, name).manifest()}
                output_path = write_manifest(kind, name, manifest)
            except Exception as exc:
                failures += 1
                print(f"failed {name}: {type(exc).__name__}: {exc}", file=sys.stderr)
                traceback.print_exc()
            else:
                print(f"wrote {output_path}")

    return int(failures > 0)


if __name__ == "__main__":
    raise SystemExit(main())
