#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import re
from lark import Lark, Transformer, v_args, Token

# ───────────────────────────── Grammar ─────────────────────────────
grammar = r"""
start: document?
document: import_* label? (table | ref) (label (table | ref))*

import_: "<!--" "import" NONLOCAL ("as" NONLOCAL)? "-->"
label : "#"+ "``" LOCAL "``"
table : PIPE_ROW PIPE_ROW PIPE_ROW+
ref   : "``" NONLOCAL "``"

NONLOCAL: /[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*/
LOCAL: /[A-Za-z_][A-Za-z0-9_]*/
PIPE_ROW: /\s*\|[^\n]*\|\s*(?:\r?\n|$)/

%ignore /[ \t]+/
%ignore /\r?\n+/
"""

# ───────────────────────────── AST Types ─────────────────────────────


@dataclass
class Field:
    name: str
    type: str
    required: bool
    description: str
    deps: List = field(default_factory=list)


@dataclass
class Model:
    label: str
    fields: List[Field] = field(default_factory=list)
    ref: Optional[str] = None


@dataclass
class Namespace:
    path: str
    imports: Dict[str, str] = field(default_factory=dict)
    models: List[Model] = field(default_factory=list)


# ───────────────────────────── Helpers ─────────────────────────────
TYPE_REF_RE = re.compile(r"``([A-Za-z_][A-Za-z0-9_.]*)``")


def split_row(line: str) -> List[str]:
    """Split Markdown table row by unescaped pipes."""
    inner = line.strip()[1:-1]
    parts, buf, esc = [], [], False
    for ch in inner:
        if esc:
            buf.append(ch)
            esc = False
        elif ch == "\\":
            esc = True
        elif ch == "|":
            parts.append("".join(buf).replace(r"\|", "|").strip())
            buf = []
        else:
            buf.append(ch)
    parts.append("".join(buf).replace(r"\|", "|").strip())
    return parts


def truthy_required(s: str) -> bool:
    return s.strip().lower() in {"yes", "true", "required", "y", "1"}


# ───────────────────────────── Transformer ─────────────────────────────
@v_args(inline=True)
class ModelSchemaTransformer(Transformer):
    ns: Namespace
    current_label: Optional[str]

    def __init__(self, namespace: str) -> None:
        super().__init__()
        self.ns = Namespace(namespace)
        self.current_label = None

    def start(self, doc: Optional[Namespace] = None) -> Optional[Namespace]:
        return doc or self.ns

    def document(self, *_) -> Namespace:
        return self.ns

    # ───────────── import / label / ref / table ─────────────
    def import_(self, src: Token, *rest: Token) -> None:
        alias = rest[1] if len(rest) == 3 else None
        name: str = src.value
        self.ns.imports[alias.value if alias else name.split(".")[-1]] = name

    def label(self, name: Token) -> str:
        self.current_label = str(name.value)
        return self.current_label

    def ref(self, name: Token) -> None:
        label = self.current_label or "<main>"
        self.ns.models.append(Model(label=label, ref=name.value))
        self.current_label = None

    def table(self, header: Token, sep: Token, *rows: Token) -> None:
        fields: List[Field] = []
        for r in rows:
            cells = split_row(r.value)
            if len(cells) != 4:
                raise ValueError(f"Invalid table row: {r.value}")
            fname, ftype, freq, fdesc = cells
            fields.append(
                Field(
                    name=fname,
                    type=ftype,
                    required=truthy_required(freq),
                    description=fdesc,
                    deps=list(dict.fromkeys(TYPE_REF_RE.findall(ftype))),
                )
            )
        label = self.current_label or "<main>"
        self.ns.models.append(Model(label=label, fields=fields))
        self.current_label = None


# ───────────────────────────── Runner ─────────────────────────────
if __name__ == "__main__":
    src = """\
<!-- import ya.Image as Image -->

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| id | string | yes | Unique identifier |
| texture | array[``test.Texture``] | yes | Linked texture |

## ``Texture``
``Image``
"""
    parser = Lark(grammar, parser="lalr", regex=True)
    tree = parser.parse(src)
    ns = ModelSchemaTransformer("demo").transform(tree)

    import json

    print(json.dumps(ns, default=lambda o: o.__dict__, indent=2))
