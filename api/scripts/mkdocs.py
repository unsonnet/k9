#!/usr/bin/env python3

import argparse
import ast
import importlib
import json
import subprocess
import sys
import tempfile
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFESTS = ROOT / "infra/cdk/cdk.out/manifests"
START = "    # BEGIN GENERATED PARTIAL SIGNATURE"
END = "    # END GENERATED PARTIAL SIGNATURE"
IMPORTS = (
    "from typing import TYPE_CHECKING, Self\n"
    "from k9.types.base import Partial\n"
    "from k9.types.common import missing\n"
)
KINDS = ("services", "workers")


def generate_partial(path: Path) -> str | None:
    original = path.read_text()
    lines = original.splitlines(keepends=True)

    # Remove previously generated signatures.
    clean = []
    generating = False
    for line in lines:
        if line.rstrip() == START:
            if generating:
                raise ValueError(f"Nested generated block: {path}")
            generating = True
        elif line.rstrip() == END:
            if not generating:
                raise ValueError(f"Unexpected generated block end: {path}")
            generating = False
        elif not generating:
            clean.append(line)

    if generating:
        raise ValueError(f"Unclosed generated block: {path}")

    source = "".join(clean)
    tree = ast.parse(source, filename=str(path))
    insertions = []

    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        if not any(
            isinstance(base, ast.Name) and base.id == "ResourceModel"
            for base in node.bases
        ):
            continue

        fields = [
            (field.target.id, field.annotation, field.end_lineno)
            for field in node.body
            if isinstance(field, ast.AnnAssign) and isinstance(field.target, ast.Name)
        ]
        if not fields:
            raise ValueError(f"No fields in {node.name}: {path}")
        end_lineno = fields[-1][2]
        if end_lineno is None:
            raise ValueError(f"Missing field end line in {node.name}: {path}")

        signature = [
            START,
            "    if TYPE_CHECKING:",
            "",
            "        @classmethod",
            "        def partial(",
            "            cls,",
            "            *,",
            *(
                f"            {name}: {ast.unparse(annotation)} | missing = ...,"
                for name, annotation, _ in fields
            ),
            "        ) -> Partial[Self]: ...",
            END,
        ]
        insertions.append((end_lineno, "\n".join(signature)))

    if not insertions:
        return source if source != original else None

    for line_number, signature in reversed(insertions):
        clean.insert(line_number, f"\n{signature}\n")

    source = "".join(clean)

    # Add imports after the module docstring and future imports.
    if not all(line in source for line in IMPORTS.splitlines()):
        tree = ast.parse(source, filename=str(path))
        position = 0
        for index, node in enumerate(tree.body):
            if (
                index == 0
                and isinstance(node, ast.Expr)
                and isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, str)
            ):
                pass
            elif not (isinstance(node, ast.ImportFrom) and node.module == "__future__"):
                break
            if node.end_lineno is None:
                raise ValueError(f"Missing import end line: {path}")
            position = node.end_lineno
        lines = source.splitlines(keepends=True)
        lines.insert(position, IMPORTS)
        source = "".join(lines)

    return source


def generate_partials() -> None:
    for path in sorted((ROOT / "types").glob("*/src/**/*.py")):
        source = generate_partial(path)
        if source is None:
            continue

        # Format in a temporary file before replacing the original.
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", dir=path.parent, delete=False
        ) as temp:
            temp.write(source)
            tmp = Path(temp.name)

        try:
            subprocess.run(
                ["ruff", "check", "--select", "I", "--fix", str(tmp)],
                check=True,
            )
            subprocess.run(["ruff", "format", str(tmp)], check=True)

            formatted = tmp.read_text()
            if formatted != path.read_text():
                path.write_text(formatted)
                print(f"updated {path.relative_to(ROOT)}")
        finally:
            tmp.unlink()


def discover(kind: str) -> dict[str, Path]:
    packages = {}
    for path in sorted((ROOT / kind).glob("*/src/k9/" + kind + "/*/__init__.py")):
        name = path.parent.name
        if name in packages:
            raise ValueError(f"Duplicate {kind} package: {name}")
        packages[name] = path.parents[3]
    return packages


def generate_manifests(kind: str, packages: dict[str, Path]) -> int:
    if not packages:
        return 0

    output_dir = MANIFESTS / kind
    output_dir.mkdir(parents=True, exist_ok=True)

    for path in output_dir.glob("*.json"):
        path.unlink()

    failures = 0
    for name, src in packages.items():
        try:
            if str(src) not in sys.path:
                sys.path.insert(0, str(src))

            module = importlib.import_module(f"k9.{kind}.{name}")
            app = module.app
            manifest = {kind: name, **app.manifest()}

            output = output_dir / f"{name}.json"
            output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
            print(f"wrote {output.relative_to(ROOT)}")

        except Exception:
            failures += 1
            traceback.print_exc()

    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--list", action="store_true", help="List discovered packages")
    args = parser.parse_args()

    packages = {kind: discover(kind) for kind in KINDS}

    if args.list:
        for kind, found in packages.items():
            print(f"{kind}:")
            for name in found:
                print(f"  {name}")
        return 0

    if not any(packages.values()):
        parser.error("No services or workers found")

    generate_partials()
    failures = sum(generate_manifests(kind, found) for kind, found in packages.items())
    return int(failures > 0)


if __name__ == "__main__":
    raise SystemExit(main())
