#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
parser.py
Front-end parser for ModelSchema and REST API specifications.

Overview
--------
The parser scans a project directory containing Markdown-based schema
definitions and endpoint documentation. It parses each file using Lark grammars
to produce strongly typed dataclass representations of models and methods.

Responsibilities
----------------
• Parse `models/*.md` → schema.Namespace objects via the ModelSchema grammar
• Parse `endpoints/*.md` → method.Method objects via the REST API grammar
• Assign deterministic namespace labels based on directory structure
• Record non-fatal syntax or semantic errors for review
• Produce clean dataclass graphs for downstream linking and generation

Input Directory Layout
----------------------
root/
 ├─ models/        # ModelSchema Markdown files
 │   └─ product.md
 └─ endpoints/     # REST API Markdown files
     └─ report/POST.md

Namespace Labeling
------------------
• Models:    relative path under `models/`   → dotted path (e.g. `product.series`)
• Endpoints: relative path under `endpoints/` → prefixed with `api.` (e.g. `api.report.POST`)

Output
------
parse_project(root_dir) → (namespaces, methods, errors)

    namespaces : List[schema.Namespace]
    methods    : List[method.Method]
    errors     : List[str]

Each namespace and method is a fully structured dataclass instance; no JSON
serialization or dependency resolution occurs at this stage.

Usage
-----
This module provides importable library functions and is invoked by `__main__.py`:

    from parser import parse_project, _to_jsonable

Design Notes
------------
Parsing is deterministic, LALR-based (via Lark), and non-mutating.
The parser performs syntactic and structural validation only; dependency
resolution and import inlining are handled by `linker.py` in the next stage.
"""

from __future__ import annotations
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import List, Tuple, Any

from lark import Lark

from .schema import grammar as schema_grammar, ModelSchemaTransformer, Namespace
from .method import grammar as api_grammar, RestApiTransformer, Method
from .errors import ParseError


# ───────────────────────────── Helper Functions ─────────────────────────────


def _rel_ns_label(file_path: Path, base_dir: Path) -> str:
    """Convert 'base_dir/.../name.md' into a dotted namespace label like '.../name'."""
    rel = file_path.relative_to(base_dir).with_suffix("")
    return ".".join(rel.parts)


def _read_text(path: Path) -> str:
    """Read UTF-8 text from a file."""
    return path.read_text(encoding="utf-8")


def _walk_md(root: Path) -> List[Path]:
    """Return all Markdown (.md) files under a directory."""
    return [p for p in root.rglob("*.md") if p.is_file()]


# ───────────────────────────── Core Parsing ─────────────────────────────


def parse_project(
    root_dir: Path, strict: bool = False
) -> Tuple[List[Namespace], List[Method], List[str]]:
    """
    Parse all ModelSchema and REST API Markdown files beneath a project root.

    Parameters
    ----------
    root_dir : Path
        Directory containing 'models/' and/or 'endpoints/' subdirectories.
    strict : bool
        If True, raises immediately on the first parse error.
        If False, continues parsing and collects all errors.

    Returns
    -------
    Tuple[List[Namespace], List[Method], List[str]]
        namespaces : all parsed model namespaces
        methods    : all parsed REST endpoints
        errors     : list of parsing error messages
    """
    errors: List[str] = []
    namespaces: List[Namespace] = []
    methods: List[Method] = []

    models_dir = root_dir / "models"
    endpoints_dir = root_dir / "endpoints"

    # ── Parse model definitions ───────────────────────────────────────────
    if models_dir.is_dir():
        for md_file in sorted(_walk_md(models_dir)):
            ns_label = _rel_ns_label(md_file, models_dir)
            try:
                text = _read_text(md_file)
                parser = Lark(schema_grammar, parser="lalr", regex=True)
                tree = parser.parse(text)
                namespace = ModelSchemaTransformer(namespace=ns_label, source_file=str(md_file)).transform(tree)
                namespaces.append(namespace)
            except Exception as e:
                error_msg = f"Failed to parse model schema: {e}"
                parse_error = ParseError(error_msg, str(md_file))
                if strict:
                    raise parse_error
                errors.append(str(parse_error))

    # ── Parse REST endpoint definitions ──────────────────────────────────
    if endpoints_dir.is_dir():
        for md_file in sorted(_walk_md(endpoints_dir)):
            api_ns = "api." + _rel_ns_label(md_file, endpoints_dir)
            try:
                text = _read_text(md_file)
                parser = Lark(api_grammar, parser="lalr", regex=True)
                tree = parser.parse(text)
                method = RestApiTransformer(
                    namespace=api_ns, filename=str(md_file)
                ).transform(tree)
                methods.append(method)
            except Exception as e:
                error_msg = f"Failed to parse REST API endpoint: {e}"
                parse_error = ParseError(error_msg, str(md_file))
                if strict:
                    raise parse_error
                errors.append(str(parse_error))

    return namespaces, methods, errors


# ───────────────────────────── JSON Serialization ─────────────────────────────


def _to_jsonable(obj: Any) -> Any:
    """
    Recursively convert dataclass graphs into JSON-serializable structures.

    • dataclasses → dict
    • dict        → dict (values converted)
    • list/set    → list (elements converted)
    • tuple       → list
    """
    if is_dataclass(obj):
        d = asdict(obj)  # type: ignore
        return {k: _to_jsonable(v) for k, v in d.items()}

    if isinstance(obj, dict):
        return {k: _to_jsonable(v) for k, v in obj.items()}

    if isinstance(obj, (list, tuple, set)):
        seq = list(obj)
        if all(isinstance(x, str) for x in seq):
            seq = sorted(seq)
        else:
            seq = [_to_jsonable(x) for x in seq]
        return seq

    return obj
