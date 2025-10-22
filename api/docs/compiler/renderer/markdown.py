#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
renderer/markdown.py
Parses the same linked Method → Payload → Response hierarchy as html.py,
but renders Markdown with consistent quote-level indentation and nested
schema tables for requests and responses alike.
"""

from __future__ import annotations
from typing import List, Optional, Dict, Set
from ..method import Method, Payload, Response, Docstring
from ..schema import Namespace, Model, Field


# ───────────────────────────── Entry ─────────────────────────────


def generate_api_markdown(methods: List[Method]) -> str:
    grouped = _group_methods_by_api(methods)
    toc = _build_global_toc(grouped)
    body = "\n\n".join(_render_api_group(group, paths) for group, paths in grouped.items())
    return f"# API Reference\n\n{toc}\n\n{body}\n"


# ───────────────────────────── Grouping ─────────────────────────────


def _group_methods_by_api(methods: List[Method]) -> Dict[str, Dict[str, List[Method]]]:
    order = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"]
    order_index = {v: i for i, v in enumerate(order)}

    grouped: Dict[str, Dict[str, List[Method]]] = {}
    for m in methods:
        seg = m.path.strip("/").split("/")[0] or "root"
        group = f"{seg.capitalize()} API"
        grouped.setdefault(group, {}).setdefault(m.path, []).append(m)

    for g in grouped.values():
        for path in g:
            g[path].sort(key=lambda m: order_index.get(m.verb.upper(), 99))

    def is_param(seg: str) -> bool:
        s = seg.strip()
        return s.startswith("{") and s.endswith("}")

    def seg_sort_tuple(seg: str) -> tuple:
        s = seg.strip()
        return (0, s.strip("{}").lower()) if is_param(s) else (1, s.lower())

    def path_sort_key(p: str) -> tuple:
        parts = [s for s in p.strip("/").split("/") if s]
        tail = parts[1:] if parts else []
        return tuple(seg_sort_tuple(seg) for seg in tail)

    return {
        group: dict(sorted(paths.items(), key=lambda kv: path_sort_key(kv[0])))
        for group, paths in sorted(grouped.items())
    }


# ───────────────────────────── TOCs ─────────────────────────────


def _build_global_toc(grouped: Dict[str, Dict[str, List[Method]]]) -> str:
    lines = ["# Table of Contents", ""]
    for group, paths in grouped.items():
        lines.append(f"- [{group}](#{_anchor(group)})")
        for path, methods in paths.items():
            for m in methods:
                lines.append(
                    f"  - [{m.verb.upper()} {path}](#{_anchor(f'{m.verb.upper()} {path}')})"
                )
    lines.append("")
    return "\n".join(lines)


def _build_inner_toc(group: str, paths: Dict[str, List[Method]]) -> str:
    lines: List[str] = ["### Table of Contents", ""]
    for path, methods in paths.items():
        for m in methods:
            lines.append(f"- [{m.verb.upper()} {path}](#{_anchor(f'{m.verb.upper()} {path}')})")
            lines.append(f"  - [Request](#{_anchor(f'{m.verb.upper()} {path} request')})")
            if m.responses:
                for r in _sorted_responses(m.responses):
                    lines.append(
                        f"  - [Response {r.code}](#{_anchor(f'{m.verb.upper()} {path} response {r.code}')})"
                    )
    lines.append("")
    lines.append(f"[Back to Top](#table-of-contents)")
    return "\n".join(lines)


# ───────────────────────────── Rendering ─────────────────────────────


def _render_api_group(group: str, paths: Dict[str, List[Method]]) -> str:
    lines = [f"# {group}\n", _build_inner_toc(group, paths), ""]
    for path, methods in paths.items():
        for m in methods:
            lines.append(_render_endpoint(m, group))
    return "\n\n".join(lines).strip()


def _render_endpoint(m: Method, group: str) -> str:
    out = [f"## {m.verb.upper()} {m.path}\n"]
    if m.doc:
        out.append(_render_docstring(m.doc, 1))

    out.append(f'<a id="{_anchor(f"{m.verb.upper()} {m.path} request")}"></a>\n### Request\n')
    out.append(_render_payload_section(m.request, "Request"))

    if m.responses:
        for r in _sorted_responses(m.responses):
            out.append(_render_response_section(m, r))
    else:
        out.append("_No responses defined._")

    out.append(f"\n[Back to {group}](#{_anchor(group)})")
    return "\n\n".join(out).strip()


def _render_payload_section(p: Optional[Payload], title: str) -> str:
    if not p:
        return "_No payload defined._"

    lines: List[str] = []
    if p.doc:
        lines.append(_render_docstring(p.doc, 1))

    for label, doc in [
        ("Headers", p.headers),
        ("Path Parameters", p.path),
        ("Query Parameters", p.query),
        ("Body", p.body),
    ]:
        if doc:
            lines.append(f"#### {label}")
            if label == "Body" and p.ctype:
                lines.append(f"##### Content-Type: `{p.ctype}`\n")
            lines.append(_render_docstring(doc, 1))
    return "\n\n".join(lines).strip()


def _render_response_section(m: Method, r: Response) -> str:
    aid = _anchor(f"{m.verb.upper()} {m.path} response {r.code}")
    lines = [f'<a id="{aid}"></a>\n### Response {r.code}\n']
    if r.payload:
        if r.payload.doc:
            lines.append(_render_docstring(r.payload.doc, 1))
        for label, doc in [
            ("Headers", r.payload.headers),
            ("Path Parameters", r.payload.path),
            ("Query Parameters", r.payload.query),
            ("Body", r.payload.body),
        ]:
            if doc:
                lines.append(f"#### {label}")
                if label == "Body" and r.payload.ctype:
                    lines.append(f"##### Content-Type: `{r.payload.ctype}`\n")
                lines.append(_render_docstring(doc, 1))
    return "\n\n".join(lines).strip()


# ───────────────────────────── Docstring + Schema Rendering ─────────────────────────────


def _render_docstring(doc: Optional[Docstring], level: int = 1, visited: Optional[Set[str]] = None) -> str:
    if not doc:
        return ""
    visited = visited or set()
    out: List[str] = []

    text_blocks = [b.strip() for b in doc if isinstance(b, str) and b.strip()]
    if text_blocks:
        for tb in text_blocks:
            out.append(_indent_block(tb, level))

    for block in doc:
        if isinstance(block, Namespace):
            for model in block.models:
                if model.label == "<main>":
                    out.append(_render_model_block(model, level, visited))
    return "\n\n".join(out).strip()


def _render_model_block(model: Model, level: int, visited: Set[str]) -> str:
    if model.label in visited:
        return ""
    visited.add(model.label)
    prefix = "> " * level
    lines = [f"{prefix}| Field | Type | Required | Description |",
             f"{prefix}|:------|:-----|:--------:|:------------|"]
    for f in model.fields:
        req = "✅" if f.required else "—"
        lines.append(f"{prefix}| **{f.name}** | {_esc(f.type)} | {req} | {f.description or ''} |")
    for f in model.fields:
        for dep in f.deps or []:
            if isinstance(dep, Model) and dep.label not in visited:
                lines.append("")
                lines.append(f"{prefix}> **{dep.label} schema**")
                lines.append(_render_model_block(dep, level + 1, visited))
    return "\n".join(lines)


# ───────────────────────────── Utilities ─────────────────────────────


def _esc(text: str) -> str:
    return text.replace("|", "\\|")


def _sorted_responses(responses: List[Response]) -> List[Response]:
    return sorted(responses, key=lambda r: r.code)


def _indent_block(text: str, level: int = 1) -> str:
    prefix = "> " * level
    return "\n".join(prefix + line for line in text.splitlines())


def _anchor(text: str) -> str:
    import re
    slug = (
        text.lower()
        .translate(str.maketrans("", "", "`/(){}.,→"))
        .strip()
    )
    return re.sub(r"\s+", "-", slug)
