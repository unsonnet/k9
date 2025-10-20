#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Union
from lark import Lark, Transformer, v_args, Token

from .schema import grammar as schema_grammar, ModelSchemaTransformer, Namespace

# ───────────────────────────── Grammar ─────────────────────────────
grammar = r"""
start: document?
document: method docstring? request response+

method: "#" METHOD "`" PATH "`"
request: "##" "Request" payload
response: "##" "Response" CODE payload

payload: docstring? headers? path_params? query_params? body?
headers: "###" "Headers" docstring
path_params: "###" "Path Parameters" docstring
query_params: "###" "Query Parameters" docstring
body: "###" "Body" "(`" CONTENT_TYPE "`)" docstring

docstring: (schema | paragraph)+
schema: "<!-- Schema Begin -->" SCHEMA_CONTENT "<!-- Schema End -->"
paragraph: /([^#<\n][^\n]*\n?)+/

METHOD: /(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)/
PATH: /[^`]+/
CODE: /\d{3}/
CONTENT_TYPE: /[A-Za-z0-9_\-\/\+\.]+/
SCHEMA_CONTENT: /(?s)(?:(?!<!-- Schema End -->).)+/

%ignore /[ \t]+/
%ignore /\r?\n+/
"""

# ───────────────────────────── AST Types ─────────────────────────────

Markdown = Union[str, Namespace]
Docstring = List[Markdown]


@dataclass
class Payload:
    doc: Optional[Docstring] = None
    headers: Optional[Docstring] = None
    path: Optional[Docstring] = None
    query: Optional[Docstring] = None
    body: Optional[Docstring] = None
    ctype: Optional[str] = None


@dataclass
class Response:
    code: int
    payload: Payload


@dataclass
class Method:
    verb: str
    path: str
    doc: Optional[Docstring]
    request: Payload
    responses: List[Response] = field(default_factory=list)


# ───────────────────────────── Helpers ─────────────────────────────
def parse_schema_block(
    src: str, namespace: str, filename: str = "<input>"
) -> Namespace:
    """Parse a ModelSchema block inline."""
    parser = Lark(schema_grammar, parser="lalr", regex=True)
    tree = parser.parse(src.strip())
    return ModelSchemaTransformer(namespace, source_file=filename).transform(tree)


# ───────────────────────────── Transformer ─────────────────────────────
@v_args(inline=True)
class RestApiTransformer(Transformer):
    namespace: str
    filename: str
    schema_count: int

    def __init__(self, namespace: str, filename: str = "<input>") -> None:
        super().__init__()
        self.namespace = namespace
        self.filename = filename
        self.schema_count = 0

    def start(self, doc: Optional[Method] = None) -> Optional[Method]:
        return doc

    def document(self, method_pair: tuple[str, str], *parts: object) -> Method:
        verb, path = method_pair
        doc: Optional[Docstring] = None
        request: Optional[Payload] = None
        responses: List[Response] = []

        for p in parts:
            if isinstance(p, list):  # Docstring
                doc = p
            elif isinstance(p, Payload) and request is None:
                request = p
            elif isinstance(p, Response):
                responses.append(p)

        if request is None:
            request = Payload()
        return Method(
            verb=verb, path=path, doc=doc, request=request, responses=responses
        )

    # ───────────── method / request / response ─────────────
    def method(self, method_tok: Token, path_tok: Token) -> tuple[str, str]:
        """# GET `/api/path`"""
        return method_tok.value, path_tok.value

    def request(self, payload: Payload) -> Payload:
        return payload

    def response(self, code_tok: Token, payload: Payload) -> Response:
        return Response(code=int(code_tok.value), payload=payload)

    # ───────────── payload + sub-sections ─────────────
    def payload(self, *parts: object) -> Payload:
        p = Payload()
        for part in parts:
            if isinstance(part, list):  # Docstring
                if p.doc is None:
                    p.doc = part
            elif isinstance(part, Payload):
                if part.headers:
                    p.headers = part.headers
                if part.path:
                    p.path = part.path
                if part.query:
                    p.query = part.query
                if part.body:
                    p.body = part.body
                    p.ctype = part.ctype
        return p

    def headers(self, doc: Docstring) -> Payload:
        return Payload(headers=doc)

    def path_params(self, doc: Docstring) -> Payload:
        return Payload(path=doc)

    def query_params(self, doc: Docstring) -> Payload:
        return Payload(query=doc)

    def body(self, ctype_tok: Token, doc: Docstring) -> Payload:
        return Payload(body=doc, ctype=ctype_tok.value)

    # ───────────── docstring / schema / paragraph ─────────────
    def docstring(self, *blocks: Union[str, Namespace]) -> Docstring:
        return list(blocks)

    def paragraph(self, tok: Token) -> str:
        return tok.value.strip()

    def schema(self, content: Token) -> Namespace:
        self.schema_count += 1
        label = f"{self.namespace}.Schema{self.schema_count:02d}"
        return parse_schema_block(content.value, label, self.filename)


# ───────────────────────────── Runner ─────────────────────────────
if __name__ == "__main__":
    src = """\
# GET `/api/v1/items`

List all items.

<!-- Schema Begin -->
| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| id | string | yes | ID |
| name | string | yes | Name |
<!-- Schema End -->

## Request
### Query Parameters
<!-- Schema Begin -->
| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| limit | integer | no | Max items |
<!-- Schema End -->

## Response 200
### Body (`application/json`)
<!-- Schema Begin -->
| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| items | array[``demo.Item``] | yes | Items list |
<!-- Schema End -->
"""

    parser = Lark(grammar, parser="lalr", regex=True)
    tree = parser.parse(src)
    api = RestApiTransformer("api", filename="api.md").transform(tree)

    import json

    print(
        json.dumps(
            api,
            default=lambda o: list(o) if isinstance(o, set) else o.__dict__,
            indent=2,
        )
    )
