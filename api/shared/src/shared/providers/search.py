import base64
import json
from collections.abc import Iterable
from dataclasses import dataclass
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

from ..config import GrantSpec, settings
from ..errors import DomainForbidden, DomainInvariantViolation, DomainNotFound
from ..helpers import sanitize_query
from . import BaseProvider, ExceptionMap, apimethod

__all__ = [
    "Term",
    "Text",
    "Near",
    "Page",
    "SearchProvider",
]


@dataclass(frozen=True, slots=True)
class Term:
    field: str
    options: list[str] | None

    def apply(
        self,
        *,
        should: list[dict[str, Any]],
        filters: list[dict[str, Any]],
    ) -> None:
        if self.options:
            filters.append({"terms": {self.field: self.options}})


@dataclass(frozen=True, slots=True)
class Text:
    field: str
    query: str | None

    def apply(
        self,
        *,
        should: list[dict[str, Any]],
        filters: list[dict[str, Any]],
    ) -> None:
        if q := sanitize_query(self.query or ""):
            should.extend(
                [
                    {
                        "multi_match": {
                            "query": q,
                            "fields": [f"{self.field}^5", f"{self.field}.wdg^4"],
                            "type": "best_fields",
                            "operator": "and",
                        }
                    },
                    {
                        "multi_match": {
                            "query": q,
                            "fields": [
                                f"{self.field}.sat",
                                f"{self.field}.sat._2gram",
                                f"{self.field}.sat._3gram",
                            ],
                            "type": "bool_prefix",
                            "boost": 2,
                        }
                    },
                    {
                        "multi_match": {
                            "query": q,
                            "fields": [f"{self.field}^2", f"{self.field}.wdg"],
                            "type": "best_fields",
                            "operator": "and",
                            "fuzziness": "AUTO",
                            "prefix_length": 1,
                            "max_expansions": 25,
                            "boost": 0.4,
                        }
                    },
                ]
            )


@dataclass(frozen=True, slots=True)
class Near:
    field: str
    coord: tuple[float, float, int] | None

    def apply(
        self,
        *,
        should: list[dict[str, Any]],
        filters: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        if self.coord is not None:
            lat, lon, radius = self.coord
            geo = {f"{self.field}.geo": {"lat": lat, "lon": lon}}
            filters.append({"geo_distance": {"distance": f"{radius}km", **geo}})
            return geo


type Query = Term | Text | Near


@dataclass(frozen=True, slots=True)
class Page[T]:
    items: list[T]
    cursor: str | None

    def hydrate[M: BaseModel](self, model: type[M]) -> "Page[M]":
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
        *queries: Query,
        limit: int,
        cursor: str | None,
    ) -> Page[dict[str, Any]]:
        return self._page(
            self._os.search(
                body=self._search_body(
                    queries=queries,
                    limit=limit,
                    cursor=cursor,
                ),
                index=self._idx,
            ),
            limit=limit,
        )

    @apimethod
    def index_document(
        self,
        *,
        type: str,
        id: str,
        **attrs: Any,
    ) -> None:
        root_type, root_id = self._root(type=type, id=id)
        if (type, id) == (root_type, root_id):
            self._os.index(
                index=self._idx,
                id=root_id,
                body={"type": type, "id": id, **attrs},
                params={"refresh": "wait_for"},
            )
            return None

        (*parent_types, field), (*parent_ids, item_id) = self._path(type=type, id=id)
        self._os.update(
            index=self._idx,
            id=root_id,
            body={
                "script": {
                    "lang": "painless",
                    "source": self._upsert_script(),
                    "params": {
                        "parent_types": parent_types,
                        "parent_ids": parent_ids,
                        "field": f".{field}",
                        "item": {"id": item_id, "type": type, **attrs},
                    },
                }
            },
            params={"refresh": "wait_for"},
        )
        return None

    @apimethod
    def update_document(
        self,
        *,
        type: str,
        id: str,
        **attrs: Any,
    ) -> None:
        root_type, root_id = self._root(type=type, id=id)
        if (type, id) == (root_type, root_id):
            self._os.update(
                index=self._idx,
                id=root_id,
                body={"doc": attrs},
                params={"refresh": "wait_for"},
            )
            return None

        (*parent_types, field), (*parent_ids, item_id) = self._path(type=type, id=id)
        self._os.update(
            index=self._idx,
            id=root_id,
            body={
                "script": {
                    "lang": "painless",
                    "source": self._upsert_script(),
                    "params": {
                        "parent_types": parent_types,
                        "parent_ids": parent_ids,
                        "field": f".{field}",
                        "item": {"id": item_id, "type": type, **attrs},
                    },
                }
            },
            params={"refresh": "wait_for"},
        )
        return None

    @apimethod
    def delete_document(
        self,
        *,
        type: str,
        id: str,
    ) -> None:
        root_type, root_id = self._root(type=type, id=id)
        if (type, id) == (root_type, root_id):
            self._os.delete(
                index=self._idx,
                id=id,
                params={"refresh": "wait_for"},
            )
            return None

        (*parent_types, field), (*parent_ids, item_id) = self._path(type=type, id=id)
        self._os.update(
            index=self._idx,
            id=root_id,
            body={
                "script": {
                    "lang": "painless",
                    "source": self._delete_script(),
                    "params": {
                        "parent_types": parent_types,
                        "parent_ids": parent_ids,
                        "field": f".{field}",
                        "id": item_id,
                    },
                }
            },
            params={"refresh": "wait_for"},
        )
        return None

    # ──── Private Methods ────

    @staticmethod
    def _root(*, type: str, id: str) -> tuple[str, str]:
        return type.split(".", 1)[0], id.split(".", 1)[0]

    @staticmethod
    def _path(*, type: str, id: str) -> tuple[list[str], list[str]]:
        return type.split(".")[1:], id.split(".")[1:]

    @staticmethod
    def _upsert_script() -> str:
        return """
            def node = ctx._source;
            for (int depth = 0; depth < params.parent_types.size(); depth++) {
                def field = '.' + params.parent_types[depth];
                def items = node[field];
                if (items == null) {
                    throw new IllegalArgumentException('Missing parent collection: ' + field);
                }
                boolean found = false;
                for (item in items) {
                    if (item.id == params.parent_ids[depth]) {
                        node = item;
                        found = true;
                        break;
                    }
                }
                if (!found) {
                    throw new IllegalArgumentException('Missing parent item: ' + params.parent_ids[depth]);
                }
            }
            if (node[params.field] == null) {
                node[params.field] = [];
            }
            for (item in node[params.field]) {
                if (item.id == params.item.id) {
                    for (entry in params.item.entrySet()) {
                        item[entry.getKey()] = entry.getValue();
                    }
                    return;
                }
            }
            node[params.field].add(params.item);
        """

    @staticmethod
    def _delete_script() -> str:
        return """
            def node = ctx._source;
            for (int depth = 0; depth < params.parent_types.size(); depth++) {
                def field = '.' + params.parent_types[depth];
                def items = node[field];
                if (items == null) {
                    throw new IllegalArgumentException('Missing parent collection: ' + field);
                }
                boolean found = false;
                for (item in items) {
                    if (item.id == params.parent_ids[depth]) {
                        node = item;
                        found = true;
                        break;
                    }
                }
                if (!found) {
                    throw new IllegalArgumentException('Missing parent item: ' + params.parent_ids[depth]);
                }
            }
            if (node[params.field] != null) {
                node[params.field].removeIf(item -> item.id == params.id);
            }
        """

    def _search_body(
        self,
        *,
        queries: tuple[Query, ...],
        limit: int,
        cursor: str | None,
    ) -> dict[str, Any]:
        should: list[dict[str, Any]] = []
        filters: list[dict[str, Any]] = []
        geo: dict[str, Any] | None = None

        for query in queries:
            if query_geo := query.apply(should=should, filters=filters):
                if geo is not None:
                    raise DomainInvariantViolation("Only one Near query is supported")
                geo = query_geo

        clauses: dict[str, Any] = {}
        if should:
            clauses["should"] = should
            clauses["minimum_should_match"] = 1
        if filters:
            clauses["filter"] = filters

        sort: list[dict[str, Any]] = []
        if should:
            sort.append({"_score": {"order": "desc"}})
        if geo:
            sort.append(
                {
                    "_geo_distance": {
                        **geo,
                        "order": "asc",
                        "unit": "km",
                        "mode": "min",
                        "distance_type": "arc",
                    }
                }
            )
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
        payload = payload.encode("utf-8")
        return base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")

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
                cursor = None
                match hits:
                    case [*_, {"sort": list(sort)}] if len(hits) == limit:
                        cursor = cls._encode_cursor(sort)
                return Page(
                    items=[cls._hit(hit) for hit in hits],
                    cursor=cursor,
                )
        raise DomainInvariantViolation(f"Unexpected opensearch response: {response}")

    @staticmethod
    def _hit(raw: Any, /) -> dict[str, Any]:
        match raw:
            case {
                "_source": {"id": str(id), **source},
                "_score": int() | float() | None as score,
            }:
                return {
                    "id": id,
                    **source,
                    ".score": float(score) if score is not None else None,
                }
        raise DomainInvariantViolation(f"Unexpected opensearch hit: {raw}")
