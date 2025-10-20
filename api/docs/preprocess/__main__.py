#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
__main__.py
Unified CLI entrypoint for the ModelSchema toolchain.

Pipeline
--------
  1. parse   → read Markdown sources → Namespace + Method dataclasses
  2. link    → dereference models/imports → self-contained graph
  3. compile → render unified API documentation (Markdown or HTML)

CLI
---
  python -m api --root ./path/to/project [--output api.md] [--format markdown|html] [--strict]

Example
-------
  uv run -m api --root ../api --output api.html --format html
"""

import argparse
from pathlib import Path
import sys

from .parser import parse_project
from .linker import Index, deref_namespace, deref_method, collect_embedded_namespaces
from .compiler import markdown, html


def main():
    ap = argparse.ArgumentParser(
        description="ModelSchema build pipeline (parse → link → compile)"
    )
    ap.add_argument(
        "--root",
        type=Path,
        required=True,
        help="Project root containing models/ and endpoints/",
    )
    ap.add_argument(
        "--output",
        type=Path,
        default=Path("api.md"),
        help="Final documentation file (e.g., api.md or api.html)",
    )
    ap.add_argument(
        "--format",
        choices=["markdown", "html"],
        default="markdown",
        help="Output format (markdown or html)",
    )
    ap.add_argument(
        "--strict",
        action="store_true",
        help="Fail fast on first parse or link error",
    )
    args = ap.parse_args()

    # ── 1) Parse (ModelSchema + REST API)
    print("📘 Parsing Markdown sources...")
    namespaces, methods, errors = parse_project(args.root, strict=args.strict)
    print(f"Parsed Namespaces: {len(namespaces)}")
    print(f"Parsed Methods   : {len(methods)}")
    if errors:
        print(f"⚠️  Warnings ({len(errors)}):")
        for e in errors:
            print("   ", e)
        if args.strict:
            print("❌ Strict mode enabled — aborting due to warnings.")
            sys.exit(1)

    # ── 2) Link (semantic dereferencing)
    print("🔗 Linking dependencies...")
    embedded = collect_embedded_namespaces(methods)
    index = Index(namespaces + embedded)
    linked_namespaces = [deref_namespace(ns, index) for ns in namespaces]
    linked_methods = [deref_method(m, index) for m in methods]
    print(f"Linked Namespaces: {len(linked_namespaces)}")
    print(f"Linked Methods   : {len(linked_methods)}")

    # ── 3) Compile (documentation rendering)
    print(f"🧩 Compiling documentation ({args.format})...")
    if args.format == "html":
        doc = html.generate_api_html(linked_methods)
    else:
        doc = markdown.generate_api_markdown(linked_methods)

    args.output.write_text(doc, encoding="utf-8")

    # ── 4) Summary
    print("✅ Build complete!")
    print(f"  Output format : {args.format}")
    print(f"  File written  : {args.output.resolve()}")


if __name__ == "__main__":
    main()
