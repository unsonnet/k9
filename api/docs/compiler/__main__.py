#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
__main__.py
Unified CLI entrypoint for the ModelSchema toolchain.

Pipeline
--------
  1. parse   → read Markdown sources → Namespace + Method dataclasses
  2. filter  → optionally restrict to specific API sections
  3. link    → dereference models/imports → self-contained graph
  4. compile → render unified API documentation (Markdown or HTML)

CLI
---
  python -m compiler --root ./path/to/project [--output basename] [--format markdown|html] [--strict] [--sections section1 section2 ...]

Example
-------
  uv run -m compiler --root ../api --output api --format html
  uv run -m compiler --root ../api --output product-api --sections product
  uv run -m compiler --root ../api --output user-reports --format html --sections user report
"""

import argparse
from pathlib import Path
import sys

from .parser import parse_project
from .linker import Index, deref_namespace, deref_method, collect_embedded_namespaces
from .renderer import markdown, html
from .errors import PreprocessorError


def filter_methods_by_sections(methods, sections):
    """
    Filter methods to only include those from specified sections.
    
    Args:
        methods: List of Method objects
        sections: List of section names to include (e.g., ['product', 'user'])
                 If None or empty, returns all methods
    
    Returns:
        List of filtered Method objects
    """
    if not sections:
        return methods
    
    # Normalize section names (convert to lowercase for comparison)
    sections_lower = [s.lower() for s in sections]
    
    filtered_methods = []
    for method in methods:
        # Extract the first path segment (API section)
        path_segments = method.path.strip("/").split("/")
        if path_segments and path_segments[0]:
            section = path_segments[0].lower()
            if section in sections_lower:
                filtered_methods.append(method)
    
    return filtered_methods


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
        type=str,
        default="api",
        help="Base name for output file (extension will be added automatically based on format)",
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
    ap.add_argument(
        "--sections",
        nargs="*",
        help="Restrict to specific API sections (e.g., 'product', 'user'). If not specified, all sections are included.",
    )
    args = ap.parse_args()

    # Determine output file path with appropriate extension
    extension = ".html" if args.format == "html" else ".md"
    output_path = Path(args.output + extension)

    try:
        # ── 1) Parse (ModelSchema + REST API)
        print("📘 Parsing Markdown sources...")
        namespaces, methods, errors = parse_project(args.root, strict=args.strict)
        print(f"Parsed Namespaces: {len(namespaces)}")
        print(f"Parsed Methods   : {len(methods)}")
        
        # ── 1.5) Filter methods by sections if specified
        if args.sections:
            methods = filter_methods_by_sections(methods, args.sections)
            print(f"Filtered Methods : {len(methods)} (sections: {', '.join(args.sections)})")
        
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

        output_path.write_text(doc, encoding="utf-8")

        # ── 4) Summary
        print("✅ Build complete!")
        print(f"  Output format : {args.format}")
        print(f"  File written  : {output_path.resolve()}")
        if args.sections:
            print(f"  Sections      : {', '.join(args.sections)}")
        else:
            print(f"  Sections      : all")

    except PreprocessorError as e:
        print(f"❌ {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        if args.strict:
            raise
        sys.exit(1)


if __name__ == "__main__":
    main()
