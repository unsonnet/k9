#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
compiler/markdown.py
Markdown compiler with continuous quote bars, deduped submodels,
inner TOCs per API section, and back-links for navigation.
"""

from __future__ import annotations
from typing import List, Optional, Set, Dict
from ..method import Method, Payload, Response, Docstring
from ..schema import Namespace, Model


# ───────────────────────────── Entry ─────────────────────────────


def generate_api_markdown(methods: List[Method]) -> str:
    grouped = _group_methods_by_api(methods)
    toc = _build_global_toc(grouped)
    body = "\n\n".join(
        _render_api_section(group, paths) for group, paths in grouped.items()
    )
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
        if is_param(s):
            return (0, s.strip("{}").lower())  # params first
        return (1, s.lower())  # then static, lexicographic

    def path_sort_key(p: str) -> tuple:
        parts = [s for s in p.strip("/").split("/") if s]
        tail = parts[1:] if parts else []
        key_seq = tuple(seg_sort_tuple(seg) for seg in tail)
        return key_seq

    return {
        group: dict(sorted(paths.items(), key=lambda kv: path_sort_key(kv[0])))
        for group, paths in sorted(grouped.items())
    }


# ───────────────────────────── TOC Builders ─────────────────────────────


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
    """Build inner TOC for a single API section (matches flattened hierarchy)."""
    lines: List[str] = ["### Table of Contents", ""]
    for path, methods in paths.items():
        for m in methods:
            lines.append(
                f"- [{m.verb.upper()} {path}](#{_anchor(f'{m.verb.upper()} {path}')})"
            )
            lines.append(
                f"  - [Request](#{_anchor(f'{m.verb.upper()} {path} request')})"
            )
            # dynamically list response anchors if available
            if m.responses:
                for r in _sorted_responses(m.responses):
                    lines.append(
                        f"  - [Response {r.code}](#{_anchor(f'{m.verb.upper()} {path} response {r.code}')})"
                    )
    lines.append("")
    lines.append(f"[Back to Top](#table-of-contents)")
    return "\n".join(lines)


# ───────────────────────────── Section Rendering ─────────────────────────────


def _render_api_section(group: str, paths: Dict[str, List[Method]]) -> str:
    lines = [f"# {group}\n", _build_inner_toc(group, paths), ""]
    for path, methods in paths.items():
        for m in methods:
            lines.append(_render_method(m, group))
    return "\n\n".join(lines).strip()


def _render_method(m: Method, group: str) -> str:
    out = [f"## {m.verb.upper()} {m.path}\n"]
    desc = _join_docstrings(m.doc)
    if desc:
        out.append(_indent_block(desc, 1))

    # Inject invisible anchor for "Request"
    anchor_req = _anchor(f"{m.verb.upper()} {m.path} request")
    out.append(f'<a id="{anchor_req}"></a>\n### Request\n')

    if m.request:
        req = _render_payload("Request", m.request)
        if req.startswith("### Request"):
            req = req.split("\n", 1)[1]
        out.append(req)
    else:
        out.append("_No request content._")

    # Responses (flattened)
    if m.responses:
        visited: Set[str] = set()
        for r in _sorted_responses(m.responses):
            out.append(_render_response_block(r, visited, m))
    else:
        out.append("_No responses defined._")

    out.append(f"\n[Back to {group}](#{_anchor(group)})")
    return "\n\n".join(out).strip()


# ───────────────────────────── Request / Response ─────────────────────────────


def _render_payload(title: str, p: Payload) -> str:
    lines: List[str] = []
    desc = _join_docstrings(p.doc)
    if desc:
        lines.append(_indent_block(desc, 1))

    for label, nslist in [
        ("Headers", _extract_namespaces(p.headers)),
        ("Path Parameters", _extract_namespaces(p.path)),
        ("Query Parameters", _extract_namespaces(p.query)),
        ("Body", _extract_namespaces(p.body)),
    ]:
        if nslist:
            lines.append(f"#### {label}\n")
            if label == "Body" and p.ctype:
                lines.append(f"##### Content-Type: `{p.ctype}`\n")
            visited: Set[str] = set()
            for ns in nslist:
                for model in ns.models:
                    if model.label == "<main>":
                        lines.append(_render_model_with_submodels(model, 1, visited))
    return "\n\n".join(lines).strip()


def _render_response_block(r: Response, visited: Set[str], m: Method) -> str:
    anchor_resp = _anchor(f"{m.verb.upper()} {m.path} response {r.code}")
    parts = [f'<a id="{anchor_resp}"></a>\n### Response {r.code}\n']
    desc = _join_docstrings(r.payload.doc)
    if desc:
        parts.append(_indent_block(desc, 1))
    sect = _render_payload_sections(r.payload, visited)
    if sect:
        parts.append(sect)
    return "\n\n".join(parts).strip()


def _render_payload_sections(p: Payload, visited: Set[str]) -> str:
    lines: List[str] = []
    for label, nslist in [
        ("Headers", _extract_namespaces(p.headers)),
        ("Path Parameters", _extract_namespaces(p.path)),
        ("Query Parameters", _extract_namespaces(p.query)),
        ("Body", _extract_namespaces(p.body)),
    ]:
        if nslist:
            lines.append(f"#### {label}\n")
            if label == "Body" and p.ctype:
                lines.append(f"##### Content-Type: `{p.ctype}`\n")
            for ns in nslist:
                for model in ns.models:
                    if model.label == "<main>":
                        lines.append(_render_model_with_submodels(model, 1, visited))
    return "\n\n".join(lines).strip()


# ───────────────────────────── Schema Rendering ─────────────────────────────


def _render_model_with_submodels(model: Model, level: int, visited: Set[str]) -> str:
    if model.label in visited:
        return ""
    visited.add(model.label)

    prefix = "> " * level
    lines: List[str] = []

    if model.label != "<main>":
        lines.append(f"{prefix}##### `{model.label}` schema")
        lines.append(f"{prefix}")
    lines.append(_indent_block(_render_model_table(model), level))

    for f in model.fields:
        for dep in f.deps or []:
            if isinstance(dep, Model) and dep.label and dep.label not in visited:
                lines.append(f"{prefix}")
                lines.append(_render_model_with_submodels(dep, level + 1, visited))
                lines.append(f"{prefix}")
    return "\n".join(lines).strip()


def _render_model_table(model: Model) -> str:
    lines = [
        "| Field | Type | Required | Description |",
        "|:------|:-----|:--------:|:------------|",
    ]
    for f in model.fields:
        req = "✅" if f.required else "—"
        lines.append(
            f"| **{f.name}** | {_esc(f.type)} | {req} | {f.description or ''} |"
        )
    return "\n".join(lines)


# ───────────────────────────── Utilities ─────────────────────────────


def _esc(text: str) -> str:
    return text.replace("|", "\\|")


def _extract_namespaces(doc: Optional[Docstring]) -> List[Namespace]:
    return [b for b in doc if isinstance(b, Namespace)] if doc else []


def _join_docstrings(doc: Optional[Docstring]) -> str:
    if not doc:
        return ""
    chunks = [b.strip() for b in doc if isinstance(b, str) and b.strip()]
    return "\n\n".join(chunks)


def _indent_block(text: str, level: int = 1) -> str:
    prefix = "> " * level
    lines = text.splitlines() or [text]
    return "\n".join(prefix + (ln if ln.strip() else "") for ln in lines)


def _sorted_responses(responses: List[Response]) -> List[Response]:
    return sorted(responses, key=lambda r: r.code)


def _anchor(text: str) -> str:
    import re

    slug = (
        text.lower()
        .replace("`", "")
        .replace("/", "")
        .replace("(", "")
        .replace(")", "")
        .replace("{", "")
        .replace("}", "")
        .replace(",", "")
        .replace(".", "")
        .replace("→", "")
        .strip()
    )
    return re.sub(r"\s+", "-", slug)
