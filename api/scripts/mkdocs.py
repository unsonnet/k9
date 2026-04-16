import argparse
import importlib
import sys
from pathlib import Path

from shared.http import HttpResolver


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Generate OpenAPI JSON for service handlers."
    )
    p.add_argument(
        "-s",
        "--service",
        dest="services",
        action="append",
        help="Service to generate (repeatable). Defaults to all discoverable services.",
    )
    p.add_argument(
        "--list-services", action="store_true", help="List services and exit."
    )
    p.add_argument("--output-dir", default="openapi", help="Output directory.")
    return p.parse_args()


def discover_service_names(root: Path) -> list[str]:
    return sorted(p.name for p in root.iterdir() if p.is_dir()) if root.exists() else []


def load_service_app(service: str, repo_root: Path) -> HttpResolver:
    src = repo_root / "services" / service / "src"
    if not (src / service / "handler.py").exists():
        raise FileNotFoundError(f"No handler for {service!r} at {src}")

    sys.path[:0] = [str(src)] if str(src) not in sys.path else []
    app = getattr(importlib.import_module(f"{service}.handler"), "app", None)
    if not isinstance(app, HttpResolver):
        raise TypeError(
            f"{service!r} app must be HttpResolver, got {type(app).__name__}"
        )
    return app


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    services = discover_service_names(repo_root / "services")

    if args.list_services:
        print(*services, sep="\n")
        return 0

    targets = args.services or services
    if not targets:
        print("No services found.", file=sys.stderr)
        return 1

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for service in targets:
        try:
            schema = load_service_app(service, repo_root).get_openapi_json_schema()
            path = out_dir / f"{service}.json"
            path.write_text(schema, encoding="utf-8")
            print(f"wrote {path}")
        except Exception as e:
            print(f"skip {service}: {e}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
