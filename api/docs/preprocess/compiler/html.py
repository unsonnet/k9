#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
compiler/html.py
Swagger-style HTML compiler for fully linked REST API documentation.

Purpose
-------
Produces a rich, navigable HTML API reference with a modern visual layout and
interactive schema blocks. Converts the same linked dataclasses used by the
Markdown compiler into a visually elegant, self-contained document.

Input
-----
A list of `Method` objects from the linker stage, with all schemas and imports
resolved (`Namespace`, `Model`, `Field`).

Output
------
A single self-contained HTML document featuring:
  • Sticky left-side Table of Contents (API group → methods)
  • API sections with HTTP methods rendered as primary headings
  • Clean, card-style method panels with request and response details
  • Swagger-inspired inline schema rendering
  • Collapsible submodels for nested dependencies
  • Syntax-highlighted `<code>` styling for all inline types

Features
--------
  • Smooth scroll tracking and TOC highlighting for active section
  • Strong visual separation between methods
  • Context-colored HTTP method badges (GET, POST, PUT, PATCH, DELETE, etc.)
  • Nested schema rendering using semantic HTML (`<details>` / `<summary>`)
  • **Only models labeled `<main>` are rendered at top level** — dependent
    models appear inline under their referencing field.
  • Fully responsive layout (collapsible TOC on small screens)
  • No external assets or scripts — all CSS and JS embedded inline

Design Notes
------------
  • The visual hierarchy mirrors Swagger / Redoc, but in static HTML.
  • Generated output is self-contained: portable, dark-mode friendly, and easy
    to distribute or embed in any docs portal.
"""

from __future__ import annotations
from typing import List, Optional, Dict
from html import escape as _esc
import re

from ..method import Method, Payload, Response, Docstring
from ..schema import Namespace, Model, Field


# ───────────────────────────── Entry ─────────────────────────────


def generate_api_html(methods: List[Method], *, title: str = "API Reference") -> str:
    grouped = _group_methods_by_api(methods)
    body = _render_document_body(title, grouped)
    return _wrap_html_document(title, body)


# ───────────────────────────── Grouping / Sorting ─────────────────────────────


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


# ───────────────────────────── HTML Shell ─────────────────────────────


def _wrap_html_document(title: str, body_html: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{_esc(title)}</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
:root {{
  --bg:#0b0e14; --panel:#11161f; --ink:#e6e8ee; --muted:#a9b1bd;
  --accent:#67b0ff; --accent-2:#8bd5ff; --border:#202736; --code-bg:#0f1420;
  --get:#8bd450; --post:#67b0ff; --put:#ffcc66; --patch:#c678dd;
  --delete:#ff6b6b; --opt:#a7bba9; --head:#b8c1ec;
  --radius:8px; --shadow:0 2px 8px rgba(0,0,0,0.4);
}}

html,body{{margin:0;padding:0;background:var(--bg);color:var(--ink);
font:15px/1.55 Inter,ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif;}}
a{{color:var(--accent-2);text-decoration:none;}}a:hover{{text-decoration:underline;}}

/* Layout */
body{{display:flex;min-height:100vh;}}
nav.sidebar{{position:sticky;top:0;align-self:flex-start;width:270px;height:100vh;
overflow-y:auto;background:#0d121d;border-right:1px solid var(--border);padding:1rem .8rem;}}
main.container{{flex:1;padding:2rem 3rem;max-width:1100px;margin:auto;}}

/* Headers */
.api-header h1{{font-size:2rem;margin:0 0 1rem;}}
.api-group{{margin-bottom:4rem;}}
.group-header h2{{font-size:1.5rem;margin:0 0 1.25rem;border-bottom:1px solid var(--border);padding-bottom:.35rem;}}

/* Endpoint */
.endpoint{{background:var(--panel);border:1px solid var(--border);
border-left:5px solid var(--accent-2);border-radius:var(--radius);box-shadow:var(--shadow);
padding:1.5rem 1.8rem;margin-bottom:2.5rem;transition:background .25s,border-color .25s;}}
.endpoint:hover{{background:#141b29;border-color:var(--accent);}}
.endpoint-header{{display:flex;flex-direction:column;margin-bottom:1rem;gap:.35rem;}}
.endpoint-title{{display:flex;align-items:center;gap:.5rem;font-weight:600;font-size:1.1rem;}}
.endpoint-title code{{background:var(--code-bg);padding:.15rem .4rem;border-radius:.3rem;}}
.endpoint-summary{{color:var(--muted);font-size:.95rem;}}
.endpoint-body{{display:grid;grid-template-columns:1fr 1fr;gap:2rem;}}
@media(max-width:900px){{.endpoint-body{{grid-template-columns:1fr;}}}}
.endpoint-section h3{{font-size:1rem;margin:.25rem 0 1rem;color:var(--accent-2);}}
.endpoint-section h4{{font-size:.95rem;color:var(--ink);margin:1.2rem 0 .5rem;}}
.endpoint-section h4 code{{color:var(--muted);}}
.section-content {{margin-left:.3rem;border-left: 2px solid rgba(255,255,255,.08);padding-left:.9rem;margin-bottom:1.2rem;}}

/* Response selector */
.responses .response-tabs{{display:flex;flex-wrap:wrap;align-items:center;gap:.5rem;margin:.3rem 0 1rem;}}
.responses .response-tab{{cursor:pointer;border:none;outline:none;font:inherit;border-radius:.5rem;
padding:.18rem .45rem;font-weight:700;font-size:.8rem;transition:background .15s,border-color .15s;}}
.responses .response-tab.info{{color:#9aa0aa;background:rgba(155,155,155,.1);border:1px solid rgba(155,155,155,.3);}}
.responses .response-tab.success{{color:#8bd450;background:rgba(139,212,80,.15);border:1px solid rgba(139,212,80,.3);}}
.responses .response-tab.redirect{{color:#5fb6ff;background:rgba(103,176,255,.15);border:1px solid rgba(103,176,255,.3);}}
.responses .response-tab.client{{color:#ffae42;background:rgba(255,174,66,.15);border:1px solid rgba(255,174,66,.3);}}
.responses .response-tab.server{{color:#ff6b6b;background:rgba(255,107,107,.15);border:1px solid rgba(255,107,107,.3);}}
.responses .response-tab.active.info{{background:#9aa0aa;color:#000;}}
.responses .response-tab.active.success{{background:#8bd450;color:#000;}}
.responses .response-tab.active.redirect{{background:#5fb6ff;color:#000;}}
.responses .response-tab.active.client{{background:#ffae42;color:#000;}}
.responses .response-tab.active.server{{background:#ff6b6b;color:#000;}}
.response-content{{display:none;}}
.response-content.active{{display:block;}}

/* Schema + Fields + indentation */
.doc p{{margin:.45rem 0;color:var(--muted);font-size:.95rem;line-height:1.55;}}
.submodel > .schema-block{{font-size:.95rem;border-left:2px solid rgba(255,255,255,.06);padding-left:1rem;}}
.field-block{{border-top:1px solid var(--border);padding-top:.6rem;margin-top:.6rem;}}
.field-line{{display:flex;flex-wrap:wrap;gap:.6rem;align-items:baseline;}}
.field-name{{font-weight:600;}}
.field-type code{{background:var(--code-bg);color:var(--accent-2);border-radius:.3rem;font-size:.85em;}}
.field-req.req{{color:var(--delete);font-size:.85em;margin-left:auto;}}
.field-req.opt{{color:var(--muted);font-size:.85em;font-style:italic;margin-left:auto;}}
.field-desc{{color:var(--muted);font-size:.9em;margin:0.25rem 0;}}
details.submodel summary {{cursor:pointer;color:var(--accent-2);font-size:.9em;font-weight:500;}}
details.submodel[open] summary {{color:var(--accent);}}

/* Badges (for methods) */
.badge{{display:inline-block;font-weight:700;font-size:.8rem;padding:.18rem .45rem;border-radius:.5rem;
border:1px solid var(--border);color:var(--ink);}}
.badge.get{{color:var(--get);border-color:rgba(139,212,80,.45);background:rgba(139,212,80,.12);}}
.badge.post{{color:var(--post);border-color:rgba(103,176,255,.45);background:rgba(103,176,255,.12);}}
.badge.put{{color:var(--put);border-color:rgba(255,204,102,.45);background:rgba(255,204,102,.12);}}
.badge.patch{{color:var(--patch);border-color:rgba(198,120,221,.45);background:rgba(198,120,221,.12);}}
.badge.delete{{color:var(--delete);border-color:rgba(255,107,107,.45);background:rgba(255,107,107,.12);}}
.badge.opt{{color:var(--opt);background:rgba(167,187,169,.12);}}
.badge.head{{color:var(--head);background:rgba(184,193,236,.12);}}

/* Sidebar */
.sidebar h2{{font-size:1rem;margin-top:0;color:var(--muted);}}
.sidebar ul{{list-style:none;padding-left:0;}}
.sidebar li{{margin:.35rem 0;}}
.sidebar a{{color:var(--ink);font-size:.9rem;display:block;padding:.2rem .3rem;border-radius:4px;}}
.sidebar a.active{{font-weight:600;}}
.sidebar > ul > li > ul{{margin-left:0.8rem;}}
.sidebar .toc-path{{margin-bottom:.6rem;margin-left:.8rem;}}
.sidebar .toc-path > a{{
  display:block;
  font-weight:500;
  color:var(--ink);
  font-size:.85rem;
  margin-bottom:.25rem;
  border-radius:4px;
  padding:.15rem .35rem;
  transition:background .2s,color .2s;
}}
.sidebar .toc-path > a:hover{{background:rgba(139,212,255,.08);}}
.sidebar a.active{{background:rgba(103,176,255,.18);color:var(--accent-2);}}

/* Badges (for TOC) */
.sidebar .toc-methods{{
  display:flex;
  flex-wrap:wrap;
  gap:.3rem;
  margin-left:1.4rem;
}}
.sidebar .toc-methods .badge{{
  font-size:.65rem;
  padding:.1rem .35rem;
  border-radius:.35rem;
  opacity:.8;
  transition:opacity .2s,background .2s,color .2s;
}}
.sidebar .toc-methods .badge:hover{{opacity:1;}}

/* filled when active */
.sidebar .toc-methods .badge.active.get{{background:var(--get);color:#000;}}
.sidebar .toc-methods .badge.active.post{{background:var(--post);color:#000;}}
.sidebar .toc-methods .badge.active.put{{background:var(--put);color:#000;}}
.sidebar .toc-methods .badge.active.patch{{background:var(--patch);color:#000;}}
.sidebar .toc-methods .badge.active.delete{{background:var(--delete);color:#000;}}
.sidebar .toc-methods .badge.active.opt{{background:var(--opt);color:#000;}}
.sidebar .toc-methods .badge.active.head{{background:var(--head);color:#000;}}
</style>
</head>
<body>
<nav class="sidebar"><h2>Contents</h2><ul id="toc-list"></ul></nav>
<main class="container">
{body_html}
</main>
<script>
// Sidebar TOC (grouped by path)
const toc = document.getElementById("toc-list");
document.querySelectorAll(".api-group").forEach(group => {{
  const groupName = group.querySelector(".group-header h2").textContent;
  const li = document.createElement("li");
  const a = document.createElement("a");
  a.href = "#" + group.id;
  a.textContent = groupName;
  li.appendChild(a);
  const sub = document.createElement("ul");
  sub.style.marginLeft = "0.6rem";
  const pathMap = new Map();
  group.querySelectorAll(".endpoint").forEach(ep => {{
    const title = ep.querySelector(".endpoint-title code").textContent.trim();
    const method = ep.querySelector(".endpoint-title .badge").textContent.trim();
    const eid = ep.id;
    if (!pathMap.has(title)) pathMap.set(title, []);
    pathMap.get(title).push({{ method, eid }});
  }});
  for (const [path, methods] of pathMap.entries()) {{
    const pathLi = document.createElement("li");
    pathLi.classList.add("toc-path");
    const pathA = document.createElement("a");
    pathA.href = "#" + methods[0].eid;
    pathA.textContent = path;
    pathLi.appendChild(pathA);

    const badgeRow = document.createElement("div");
    badgeRow.classList.add("toc-methods");
    methods.forEach(m => {{
      const mA = document.createElement("a");
      mA.href = "#" + m.eid;
      mA.textContent = m.method;
      mA.classList.add("badge", m.method.toLowerCase());
      badgeRow.appendChild(mA);
    }});
    pathLi.appendChild(badgeRow);
    sub.appendChild(pathLi);
  }}
  if (sub.children.length) li.appendChild(sub);
  toc.appendChild(li);
}});
// Active highlight (both links + badges)
const links = toc.querySelectorAll("a");
const sections = Array.from(document.querySelectorAll(".api-group,.endpoint"));
window.addEventListener("scroll", () => {{
  let cur = sections[0];
  for (const s of sections) {{
    const r = s.getBoundingClientRect();
    if (r.top <= 120) cur = s; else break;
  }}
  links.forEach(l => l.classList.remove("active"));
  links.forEach(l => {{
    if (l.hash === "#" + cur.id) {{
      l.classList.add("active");
      // If it’s a badge inside .toc-methods, highlight that one filled
      if (l.closest(".toc-methods")) {{
        l.classList.add("active");
      }}
    }}
  }});
}});
// Response tabs
document.querySelectorAll(".responses").forEach(resp=>{{
  const tabs=resp.querySelectorAll(".response-tab");
  const contents=resp.querySelectorAll(".response-content");
  if(tabs.length){{tabs[0].classList.add("active");contents[0].classList.add("active");}}
  tabs.forEach((tab,i)=>tab.addEventListener("click",()=>{{
    tabs.forEach(t=>t.classList.remove("active"));
    contents.forEach(c=>c.classList.remove("active"));
    tab.classList.add("active");contents[i].classList.add("active");
  }}));
}});
</script>
</body>
</html>"""


# ───────────────────────────── Rendering ─────────────────────────────


def _render_document_body(
    title: str, grouped: Dict[str, Dict[str, List[Method]]]
) -> str:
    parts = [f'<header class="api-header"><h1>{_esc(title)}</h1></header>']
    for group, paths in grouped.items():
        parts.append(_render_api_group(group, paths))
    return "\n\n".join(parts)


def _render_api_group(group: str, paths: Dict[str, List[Method]]) -> str:
    gid = _anchor(group)
    out = [f'<section class="api-group" id="{gid}">']
    out.append(f'<header class="group-header"><h2>{_esc(group)}</h2></header>')
    out.append('<div class="group-content">')
    for path, methods in paths.items():
        for m in methods:
            out.append(_render_endpoint(m))
    out.append("</div></section>")
    return "\n".join(out)


def _render_endpoint(m: Method) -> str:
    eid = _anchor(f"{m.verb.upper()} {m.path}")
    summary = _join_docstrings(m.doc)
    out = [f'<article class="endpoint" id="{eid}">']
    out.append(
        f"""<header class="endpoint-header">
  <div class="endpoint-title">{_method_badge(m.verb)} <code>{_esc(m.path)}</code></div>
  {f'<p class="endpoint-summary">{summary}</p>' if summary else ''}
</header>"""
    )
    out.append('<div class="endpoint-body">')
    if m.request:
        out.append(_render_payload_section("Request", m.request))
    if m.responses:
        out.append(_render_responses_section(m.responses))
    out.append("</div></article>")
    return "\n".join(out)


def _render_payload_section(title: str, p: Payload) -> str:
    parts = [f'<section class="endpoint-section request"><h3>{_esc(title)}</h3>']
    parts.append(_render_docstring(p.doc))
    for label, doc in [
        ("Headers", p.headers),
        ("Path Parameters", p.path),
        ("Query Parameters", p.query),
        ("Body", p.body),
    ]:
        if doc:
            if label == "Body" and p.ctype:
                label += f" <code>({_esc(p.ctype)})</code>"
            parts.append(f"<h4>{label}</h4>")
            parts.append('<div class="section-content">')
            parts.append(_render_docstring(doc))
            parts.append("</div>")
    parts.append("</section>")
    return "\n".join(parts)


def _render_responses_section(responses: List[Response]) -> str:
    parts = ['<section class="endpoint-section responses">']

    # Tab bar
    parts.append('<div class="response-tabs"><h3 style="margin:0;">Responses</h3>')
    for r in _sorted_responses(responses):
        cls = _status_class(r.code)
        parts.append(
            f'<button class="response-tab {cls}" type="button">{r.code}</button>'
        )
    parts.append("</div>")

    # Each response panel
    for r in _sorted_responses(responses):
        doc_html = _render_docstring(r.payload.doc)
        sect_html = _render_payload_sections(r.payload)
        parts.append(f'<div class="response-content">{doc_html}{sect_html}</div>')

    parts.append("</section>")
    return "\n".join(parts)


def _render_payload_sections(p: Payload) -> str:
    out = []
    for label, doc in [
        ("Headers", p.headers),
        ("Path Parameters", p.path),
        ("Query Parameters", p.query),
        ("Body", p.body),
    ]:
        if doc:
            if label == "Body" and p.ctype:
                label += f" <code>({_esc(p.ctype)})</code>"
            out.append(f"<h4>{label}</h4>")
            out.append('<div class="section-content">')
            out.append(_render_docstring(doc))
            out.append("</div>")
    return "\n".join(out)


# ───────────────────────────── Docstring + Schema Rendering ─────────────────────────────


def _render_docstring(doc: Optional[Docstring]) -> str:
    if not doc:
        return ""
    text_fragments, schema_fragments = [], []
    for chunk in doc:
        if isinstance(chunk, str):
            s = chunk.strip()
            if s:
                text_fragments.append(f"<p>{_convert_backticks(_esc(s))}</p>")
        elif isinstance(chunk, Namespace):
            for model in chunk.models:
                if model.label == "<main>":
                    schema_fragments.append(_render_model_block(model))
    out = []
    if text_fragments:
        out.append(f'<div class="doc">{"".join(text_fragments)}</div>')
    out.extend(schema_fragments)
    return "\n".join(out)


def _render_model_block(model: Model) -> str:
    parts = ['<div class="schema-block">']
    for f in model.fields:
        parts.append(_render_field_block(f))
    parts.append("</div>")
    return "\n".join(parts)


def _render_field_block(f: Field) -> str:
    req_class = "req" if f.required else "opt"
    req_label = "required" if f.required else "optional"
    type_html = _convert_backticks(_esc(f.type))
    html = [
        '<div class="field-block">',
        '<div class="field-line">',
        f'<span class="field-name">{_esc(f.name)}</span>',
        f'<span class="field-type"><code>{type_html}</code></span>',
        f'<span class="field-req {req_class}">{req_label}</span>',
        "</div>",
    ]
    if getattr(f, "description", None):
        html.append(
            f'<div class="field-desc">{_convert_backticks(_esc(f.description))}</div>'
        )
    for dep in getattr(f, "deps", None) or []:
        if isinstance(dep, Model) and dep.fields:
            html.append(
                f"""<details class="submodel">
  <summary><code>{_esc(dep.label)}</code> schema</summary>
  {_render_model_block(dep)}
</details>"""
            )
    html.append("</div>")
    return "\n".join(html)


# ───────────────────────────── Utilities ─────────────────────────────


def _convert_backticks(s: str) -> str:
    s = re.sub(r"``([^`]+)``", lambda m: f"<code>{m.group(1)}</code>", s)
    s = re.sub(r"`([^`]+)`", lambda m: f"<code>{m.group(1)}</code>", s)
    return s


def _join_docstrings(doc: Optional[Docstring]) -> str:
    """Join docstring fragments into separate paragraphs."""
    if not doc:
        return ""
    safe_fragments = [
        _convert_backticks(_esc(b.strip()))
        for b in doc
        if isinstance(b, str) and b.strip()
    ]
    return "<br><br>".join(safe_fragments)


def _sorted_responses(responses: List[Response]) -> List[Response]:
    return sorted(responses, key=lambda r: r.code)


def _anchor(text: str) -> str:
    slug = (text.lower().translate(str.maketrans("", "", "`/(){}.,→"))).strip()
    return re.sub(r"\s+", "-", slug)


def _method_badge(verb: str) -> str:
    v = verb.lower()
    cls = {
        "get": "get",
        "post": "post",
        "put": "put",
        "patch": "patch",
        "delete": "delete",
        "options": "opt",
        "head": "head",
    }.get(v, "")
    return f'<span class="badge {cls}">{_esc(verb.upper())}</span>'


def _status_class(code: int) -> str:
    if 200 <= code < 300:
        return "success"
    if 300 <= code < 400:
        return "redirect"
    if 400 <= code < 500:
        return "client"
    if 500 <= code < 600:
        return "server"
    if 100 <= code < 200:
        return "info"
    return "default"
