#!/usr/bin/env python3

from __future__ import annotations

import argparse
import importlib
import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml
from shared.http import HttpResolver

REPO_ROOT = Path(__file__).resolve().parents[1]
SERVICES_DIR = REPO_ROOT / "services"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "openapi"
SCHEMA_REF_PREFIX = "#/components/schemas/"


def service_handler_path(service: str) -> Path:
    return SERVICES_DIR / service / "src" / service / "handler.py"


def discover_services() -> list[str]:
    if not SERVICES_DIR.exists():
        return []

    return sorted(
        path.name
        for path in SERVICES_DIR.iterdir()
        if path.is_dir() and service_handler_path(path.name).exists()
    )


def import_service_app(service: str) -> HttpResolver:
    src_dir = SERVICES_DIR / service / "src"
    handler_path = service_handler_path(service)

    if not handler_path.exists():
        raise FileNotFoundError(f"Missing handler: {handler_path}")

    src_dir_str = str(src_dir)
    if src_dir_str not in sys.path:
        sys.path.insert(0, src_dir_str)

    module = importlib.import_module(f"{service}.handler")
    app = getattr(module, "app", None)

    if not isinstance(app, HttpResolver):
        raise TypeError(
            f"{service}.handler.app must be HttpResolver; got {type(app).__name__}"
        )

    return app


def load_openapi_document(service: str) -> dict[str, Any]:
    raw = import_service_app(service).get_openapi_json_schema()

    try:
        document = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{service} generated invalid OpenAPI JSON") from exc

    if not isinstance(document, dict):
        raise TypeError(f"{service} generated a non-object OpenAPI document")

    return document


def decode_pointer_token(token: str) -> str:
    return token.replace("~1", "/").replace("~0", "~")


def resolve_pointer(document: dict[str, Any], pointer: str) -> Any:
    if not pointer.startswith("#/"):
        raise ValueError(f"Only local JSON pointers are supported: {pointer}")

    value: Any = document

    for raw_token in pointer[2:].split("/"):
        token = decode_pointer_token(raw_token)

        if not isinstance(value, dict) or token not in value:
            raise KeyError(f"Could not resolve JSON pointer: {pointer}")

        value = value[token]

    return value


def inline_schema_refs(document: dict[str, Any]) -> dict[str, Any]:
    def visit(value: Any, seen_refs: tuple[str, ...] = ()) -> Any:
        if isinstance(value, list):
            return [visit(item, seen_refs) for item in value]

        if not isinstance(value, dict):
            return value

        ref = value.get("$ref")

        if isinstance(ref, str) and ref.startswith(SCHEMA_REF_PREFIX):
            if ref in seen_refs:
                return dict(value)

            resolved = deepcopy(resolve_pointer(document, ref))
            inlined = visit(resolved, seen_refs + (ref,))

            siblings = {
                key: visit(child, seen_refs)
                for key, child in value.items()
                if key != "$ref"
            }

            if siblings and isinstance(inlined, dict):
                return {**inlined, **siblings}

            return inlined

        return {key: visit(child, seen_refs) for key, child in value.items()}

    inlined = visit(document)

    if not isinstance(inlined, dict):
        raise TypeError("OpenAPI document must be a JSON object")

    components = inlined.get("components")
    if isinstance(components, dict):
        components.pop("schemas", None)
        if not components:
            inlined.pop("components", None)

    return inlined


def write_yaml_document(
    service: str,
    document: dict[str, Any],
    output_dir: Path,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / f"{service}.yaml"
    output_path.write_text(
        yaml.safe_dump(
            document,
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )

    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate OpenAPI YAML for Lambda Powertools HTTP services.",
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Directory for generated OpenAPI files. Defaults to {DEFAULT_OUTPUT_DIR}.",
    )

    parser.add_argument(
        "--list-services",
        action="store_true",
        help="List discoverable services and exit.",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    services = discover_services()

    if args.list_services:
        print(*services, sep="\n")
        return 0

    if not services:
        print("No services found.", file=sys.stderr)
        return 1

    failures = 0

    for service in services:
        try:
            document = load_openapi_document(service)
            document = inline_schema_refs(document)
            output_path = write_yaml_document(service, document, args.output_dir)
        except Exception as exc:
            failures += 1
            print(f"failed {service}: {exc}", file=sys.stderr)
        else:
            print(f"wrote {output_path}")

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
