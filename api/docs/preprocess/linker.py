#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
linker.py
Second-stage resolver for parsed ModelSchema and REST API dataclasses.

Overview
--------
After `parser.py` constructs typed Namespace and Method objects from Markdown,
the linker performs semantic resolution — replacing symbolic references and
imports with direct object links. The result is a fully self-contained,
dereferenced dataclass graph suitable for downstream code generation or export.

Responsibilities
----------------
• Clear Namespace.imports (remove alias maps)
• Resolve Model.ref → concrete Model (copy fields, preserve label)
• Replace Field.deps (List[str]) → List[Model] (fully dereferenced)
• Sanitize Field.type: convert ``a.b.C`` → `C`
• Inline all embedded Namespaces within Method request/response sections
• Preserve textual documentation (`Docstring`) exactly as written

Input
------
Dataclass objects produced by `parser.parse_project()`:
    namespaces : List[schema.Namespace]
    methods    : List[method.Method]

Output
-------
Dereferenced equivalents:
    namespaces : List[schema.Namespace]
    methods    : List[method.Method]

Usage
-----
This module is **not** a CLI. It is imported and executed by `__main__.py`
as part of the unified preprocessing pipeline:

    from linker import Index, collect_embedded_namespaces, deref_namespace, deref_method

Design Notes
------------
The linker never mutates its inputs. All dereferencing is pure-functional:
it returns new Namespace/Model/Field instances and maintains cycle detection
via `(namespace, model)` stack tracking. Only Namespace objects embedded in
Docstring structures are dereferenced — plain text is preserved verbatim.
"""

from __future__ import annotations
import re
from dataclasses import replace
from typing import Dict, List, Optional, Tuple

from .schema import Field, Model, Namespace
from .method import Payload, Response, Method, Docstring


# ───────────────────────────── Utilities ─────────────────────────────

_DBL_TICK = re.compile(r"``([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*)``")


def _sanitize_ftype(ftype: str) -> str:
    """Convert ``a.b.C`` → `C` inside a field type string."""

    def sub(m):
        return f"`{m.group(1).split('.')[-1]}`"

    return _DBL_TICK.sub(sub, ftype)


# ───────────────────────────── Embedded Namespace Collection ─────────────────────────────


def collect_embedded_namespaces(methods: List[Method]) -> List[Namespace]:
    """
    Extract all embedded Namespaces from request/response payloads within Methods.

    These include schema fragments defined inline within endpoint Markdown files.
    They are merged into the global index for consistent reference resolution.
    """
    embedded: List[Namespace] = []

    def _scan(doc):
        if not doc:
            return
        for b in doc:
            if isinstance(b, Namespace):
                embedded.append(b)

    for m in methods:
        _scan(m.doc)
        if m.request:
            _scan(m.request.doc)
            _scan(m.request.headers)
            _scan(m.request.path)
            _scan(m.request.query)
            _scan(m.request.body)
        for r in m.responses:
            _scan(r.payload.doc)
            _scan(r.payload.headers)
            _scan(r.payload.path)
            _scan(r.payload.query)
            _scan(r.payload.body)

    return embedded


# ───────────────────────────── Linking Index ─────────────────────────────


class Index:
    """Global registry for namespace and model lookups during dereferencing."""

    def __init__(self, all_ns: List[Namespace]) -> None:
        self.ns_by_path: Dict[str, Namespace] = {ns.path: ns for ns in all_ns}
        self.model_by_key: Dict[Tuple[str, str], Model] = {}
        for ns in all_ns:
            for m in ns.models:
                self.model_by_key[(ns.path, m.label)] = m

    def resolve_ref(self, ref: str, current_ns: Namespace) -> Tuple[str, str]:
        """
        Resolve a reference string relative to the current namespace.
        Examples:
            'a.b.C' → ('a.b', 'C')       (resolves import aliases)
            'C'     → (current_ns.path, 'C')
        """
        parts = ref.split(".")
        if len(parts) == 1:
            return current_ns.path, parts[0]

        ns_segs, label = parts[:-1], parts[-1]
        head = ns_segs[0] if ns_segs else None

        if head and head in current_ns.imports:
            base = current_ns.imports[head]
            ns_path = ".".join([base] + ns_segs[1:]) if len(ns_segs) > 1 else base
        else:
            ns_path = ".".join(ns_segs)
        return ns_path, label

    def get_model(self, ns_path: str, label: str) -> Model:
        """Retrieve a Model by its (namespace, label) pair, or raise a detailed KeyError."""
        try:
            return self.model_by_key[(ns_path, label)]
        except KeyError:
            avail = [m for (p, m) in self.model_by_key.keys() if p == ns_path]
            raise KeyError(
                f"Missing model: {ns_path}.{label}. Available: {', '.join(avail) or '(none)'}"
            )


# ───────────────────────────── Dereferencing Core ─────────────────────────────


def _deep_copy_field_as_linked(f: Field, new_deps: List[Model]) -> Field:
    """Return a new Field with sanitized type and linked dependency Models."""
    return Field(
        name=f.name,
        type=_sanitize_ftype(f.type),
        required=f.required,
        description=f.description,
        deps=new_deps,
    )


def _link_field_deps(
    f: Field, current_ns: Namespace, index: Index, stack: List[Tuple[str, str]]
) -> Field:
    """Replace Field.deps (List[str]) → List[Model], recursively dereferencing each."""
    if not f.deps:
        return f

    linked_models: List[Model] = []
    for dep in f.deps:
        if isinstance(dep, Model):
            linked_models.append(dep)
            continue

        dep_ns_path, dep_label = index.resolve_ref(dep, current_ns)
        dep_model = index.get_model(dep_ns_path, dep_label)
        dep_ns = index.ns_by_path.get(dep_ns_path)
        if not dep_ns:
            raise KeyError(f"Missing namespace: {dep_ns_path}")
        linked_models.append(deref_model(dep_model, dep_ns, index, stack))

    return replace(f, deps=linked_models)


def deref_model(
    src_model: Model,
    current_ns: Namespace,
    index: Index,
    stack: Optional[List[Tuple[str, str]]] = None,
) -> Model:
    """
    Return a fully dereferenced copy of a Model.

    • If `model.ref` is set, replaces it with a resolved version of the target Model.
    • Recursively expands Field.deps into concrete Model objects.
    • Prevents cyclic references through a stack-based check.
    """
    if stack is None:
        stack = []

    key = (current_ns.path, src_model.label)
    if key in stack:
        chain = " → ".join(f"{a}.{b}" for a, b in stack + [key])
        raise ValueError(f"Cycle detected while dereferencing model: {chain}")
    stack.append(key)

    # Reference model: copy target and deref its fields
    if src_model.ref:
        tgt_ns_path, tgt_label = index.resolve_ref(src_model.ref, current_ns)
        target_model = index.get_model(tgt_ns_path, tgt_label)
        target_ns = index.ns_by_path.get(tgt_ns_path)
        if not target_ns:
            raise KeyError(f"Missing namespace: {tgt_ns_path}")

        resolved = deref_model(target_model, target_ns, index, stack)
        fields = [
            _link_field_deps(
                _deep_copy_field_as_linked(f, f.deps), target_ns, index, stack
            )
            for f in resolved.fields
        ]
        stack.pop()
        return Model(label=src_model.label, fields=fields, ref=None)

    # Concrete model: link field dependencies
    fields = []
    for f in src_model.fields:
        nf = _deep_copy_field_as_linked(f, f.deps)
        fields.append(_link_field_deps(nf, current_ns, index, stack))

    stack.pop()
    return Model(label=src_model.label, fields=fields, ref=None)


def deref_namespace(ns: Namespace, index: Index) -> Namespace:
    """Return a new Namespace with imports cleared and all Models dereferenced."""
    return Namespace(
        path=ns.path,
        imports={},
        models=[deref_model(m, ns, index) for m in ns.models],
    )


def deref_ns_list(
    lst: Optional[List[Namespace]], index: Index
) -> Optional[List[Namespace]]:
    """Dereference a list of Namespaces (used for Payload components)."""
    if not lst:
        return None
    return [deref_namespace(ns, index) for ns in lst]


def deref_docstring(doc: Optional[Docstring], index: Index) -> Optional[Docstring]:
    """Dereference only Namespace elements within a Docstring list."""
    if not doc:
        return None

    new_doc: Docstring = []
    for block in doc:
        if isinstance(block, Namespace):
            new_doc.append(deref_namespace(block, index))
        else:
            new_doc.append(block)
    return new_doc


def deref_payload(p: Payload, index: Index) -> Payload:
    """Return a dereferenced copy of a Payload (safe for type checking)."""
    return Payload(
        doc=deref_docstring(p.doc, index),
        headers=deref_docstring(p.headers, index),
        path=deref_docstring(p.path, index),
        query=deref_docstring(p.query, index),
        body=deref_docstring(p.body, index),
        ctype=p.ctype,
    )


def deref_method(m: Method, index: Index) -> Method:
    """Return a dereferenced copy of a Method (including all schemas)."""
    return Method(
        verb=m.verb,
        path=m.path,
        doc=m.doc,
        request=deref_payload(m.request, index) if m.request else m.request,
        responses=[
            Response(code=r.code, payload=deref_payload(r.payload, index))
            for r in m.responses
        ],
    )
