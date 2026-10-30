from __future__ import annotations

import base64
import json
from collections.abc import Iterable
from dataclasses import dataclass
from itertools import batched
from typing import Any
from urllib.parse import urlparse

import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection
from opensearchpy.exceptions import (
    AuthenticationException,
    AuthorizationException,
    NotFoundError,
    RequestError,
)
from pydantic import BaseModel
from shared.config import settings
from shared.errors import DomainForbidden, DomainInvariantViolation, DomainNotFound
from shared.providers.base import BaseProvider, ExceptionMap, GrantSpec, apimethod

from .queries import Bool, Query, nested_path

__all__ = [
    "Page",
    "SearchProvider",
]

_WALK = """
    def node = ctx._source;
    for (key in params.path) {
        node.putIfAbsent('$' + key.type, []);
        List resource = node['$' + key.type];
        node = resource.find(item -> item.key == key);
        if (node == null) {
            return;
        }
    }
"""

_UPSERT = (
    _WALK
    + """
    node.putIfAbsent('$' + params.item.key.type, []);
    List resource = node['$' + params.item.key.type];
    node = resource.find(item -> item.key == params.item.key);
    if (node == null) {
        resource.add(params.item);
    } else {
        node.clear();
        node.putAll(params.item);
    }
"""
)


_DELETE = (
    _WALK
    + """
    List resource = node.getOrDefault('$' + params.item.key.type, []);
    resource.removeIf(item -> item.key == params.item.key);
"""
)


@dataclass(frozen=True, slots=True)
class Page[T]:
    items: list[T]
    cursor: str | None

    def hydrate[M: BaseModel](self, model: type[M]) -> Page[M]:
        return Page(
            items=[model.model_validate(item) for item in self.items],
            cursor=self.cursor,
        )


class SearchProvider(BaseProvider):
    _os: OpenSearch
    _idx: str

    def __init__(
        self,
        *,
        region: str,
        endpoint: str,
        index: str,
    ) -> None:
        parsed = urlparse(endpoint)
        if parsed.hostname is None:
            raise DomainInvariantViolation("Endpoint must include hostname")
        use_ssl = parsed.scheme != "http"
        self._os = OpenSearch(
            hosts=[
                {
                    "host": parsed.hostname,
                    "port": parsed.port or (443 if use_ssl else 80),
                }
            ],
            http_auth=settings.aws_auth(boto3.Session(region_name=region)),
            use_ssl=use_ssl,
            verify_certs=use_ssl,
            connection_class=RequestsHttpConnection,
            timeout=300,
        )
        self._idx = index

    @property
    def permissions(self) -> Iterable[GrantSpec]:
        yield GrantSpec(
            actions=(
                "es:ESHttpPost",
                "es:ESHttpPut",
                "es:ESHttpDelete",
            ),
            resources=("opensearch-domain",),
        )

    @property
    def exception_map(self) -> ExceptionMap:
        return {
            DomainForbidden: [
                AuthenticationException,
                AuthorizationException,
            ],
            DomainNotFound: [
                NotFoundError,
            ],
            DomainInvariantViolation: [
                RequestError,
            ],
        }

    # ──── Public Methods ────

    @apimethod
    def search(
        self,
        *queries: Query | None,
        limit: int,
        cursor: str | None,
    ) -> Page[dict[str, Any]]:
        body = self._body(queries, limit=limit, cursor=cursor)
        response = self._os.search(body=body, index=self._idx)
        return self._page(response, limit=limit)

    @apimethod
    def upsert(self, key: str, **attrs: Any) -> None:
        *path, leaf = self._path(key)
        item = {"key": leaf, **attrs}
        if not path:
            self._os.update(
                index=self._idx,
                id=leaf["id"],
                body={"doc": item, "doc_as_upsert": True},
                params={"refresh": "wait_for"},
            )
            return
        self._script(path, item, _UPSERT)

    @apimethod
    def delete(self, key: str) -> None:
        *path, leaf = self._path(key)
        if not path:
            self._os.delete(
                index=self._idx,
                id=leaf["id"],
                params={"refresh": "wait_for"},
            )
            return
        self._script(path, {"key": leaf}, _DELETE)

    # ──── Private Methods ────

    @staticmethod
    def _path(key: str) -> list[dict[str, Any]]:
        """Split key into root-to-leaf keys."""
        return [{"type": t, "id": i} for t, i in batched(key.split("/"), 2)]

    def _script(
        self,
        path: list[dict[str, Any]],
        item: dict[str, Any],
        source: str,
    ) -> None:
        """Run `source` on the root document, walking the keys after the root."""
        root, *path = path
        self._os.update(
            index=self._idx,
            id=root["id"],
            body={
                "script": {
                    "lang": "painless",
                    "source": source,
                    "params": {"path": path, "item": item},
                }
            },
            params={"refresh": "wait_for"},
        )

    def _body(
        self,
        queries: tuple[Query | None, ...],
        *,
        limit: int,
        cursor: str | None,
    ) -> dict[str, Any]:
        acc = Bool()
        for query in queries:
            if query is not None:
                query.apply(acc)

        clauses: dict[str, Any] = {}
        if acc.should:
            clauses |= {"should": acc.should, "minimum_should_match": 1}
        if acc.filter:
            clauses["filter"] = acc.filter

        sort: list[dict[str, Any]] = []
        if acc.should:
            sort.append({"_score": {"order": "desc"}})
        if acc.geo:
            geo = {
                "_geo_distance": {
                    **acc.geo,
                    "order": "asc",
                    "unit": "km",
                    "mode": "min",
                    "distance_type": "arc",
                }
            }
            if path := nested_path(next(iter(acc.geo))):
                geo["_geo_distance"]["nested"] = {"path": path}
            sort.append(geo)
        sort.append({"id": {"order": "asc"}})

        body: dict[str, Any] = {
            "size": limit,
            "query": {"bool": clauses} if clauses else {"match_all": {}},
            "sort": sort,
        }
        if cursor:
            body["search_after"] = self._decode_cursor(cursor)
        return body

    @staticmethod
    def _encode_cursor(sort: list[Any]) -> str:
        payload = json.dumps(sort, separators=(",", ":"), ensure_ascii=False)
        return base64.urlsafe_b64encode(payload.encode()).decode().rstrip("=")

    @staticmethod
    def _decode_cursor(cursor: str) -> list[Any]:
        try:
            payload = base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4))
            return list(json.loads(payload))
        except Exception as exc:
            raise DomainInvariantViolation(f"Unexpected cursor: {cursor}") from exc

    @classmethod
    def _page(cls, response: Any, /, limit: int) -> Page[dict[str, Any]]:
        match response:
            case {"hits": {"hits": list(hits)}}:
                match hits:
                    case [*_, {"sort": list(sort)}] if len(hits) == limit:
                        cursor = cls._encode_cursor(sort)
                    case _:
                        cursor = None
                return Page(items=[cls._hit(hit) for hit in hits], cursor=cursor)
        raise DomainInvariantViolation(f"Unexpected opensearch response: {response}")

    @staticmethod
    def _hit(raw: Any, /) -> dict[str, Any]:
        match raw:
            case {
                "_source": dict(source),
                "_score": int() | float() | None as score,
            }:
                return {
                    **source,
                    "$score": None if score is None else float(score),
                }
        raise DomainInvariantViolation(f"Unexpected opensearch hit: {raw}")
