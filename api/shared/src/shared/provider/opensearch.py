from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Self

from opensearchpy import OpenSearch


def sanitize_query(q: str) -> str | None:
    return q.replace("\\", "\\\\").replace('"', '\\"') if (q := q.strip()) else None


@dataclass(slots=True)
class Search:
    using: OpenSearch
    index: str

    _should: list[dict[str, Any]] = field(default_factory=list)
    _filter: list[dict[str, Any]] = field(default_factory=list)
    _geo: dict[str, Any] | None = None

    # ──── Private Methods ────

    def _query(self) -> dict[str, Any]:
        if not self._should and not self._filter:
            return {"match_all": {}}

        bool_query: dict[str, Any] = {}

        if self._should:
            bool_query["should"] = self._should
            bool_query["minimum_should_match"] = 1

        if self._filter:
            bool_query["filter"] = self._filter

        return {"bool": bool_query}

    def _sort(self) -> list[dict[str, Any]]:
        sort: list[dict[str, Any]] = []

        if self._should:
            sort.append({"_score": {"order": "desc"}})

        if self._geo:
            sort.append(
                {
                    "_geo_distance": {
                        **self._geo,
                        "order": "asc",
                        "unit": "km",
                        "mode": "min",
                        "distance_type": "arc",
                    }
                }
            )

        sort.append({"id": {"order": "asc"}})

        return sort

    # ──── Public Methods ────

    def key(self, field: str, *, options: list[str] | None) -> Self:
        if not options:
            return self

        self._filter.append({"terms": {field: options}})
        return self

    def text(self, field: str, *, query: str | None) -> Self:
        if query is None or (q := sanitize_query(query)) is None:
            return self

        self._should += [
            {
                "multi_match": {
                    "query": q,
                    "fields": [
                        f"{field}^5",
                        f"{field}.wdg^4",
                    ],
                    "type": "best_fields",
                    "operator": "and",
                }
            },
            {
                "multi_match": {
                    "query": q,
                    "fields": [
                        f"{field}.sat",
                        f"{field}.sat._2gram",
                        f"{field}.sat._3gram",
                    ],
                    "type": "bool_prefix",
                    "boost": 2,
                }
            },
            {
                "multi_match": {
                    "query": q,
                    "fields": [
                        f"{field}^2",
                        f"{field}.wdg",
                    ],
                    "type": "best_fields",
                    "operator": "and",
                    "fuzziness": "AUTO",
                    "prefix_length": 1,
                    "max_expansions": 25,
                    "boost": 0.4,
                }
            },
        ]

        return self

    def near(self, field: str, *, coord: tuple[float, float, int] | None) -> Self:
        if coord is None:
            return self

        self._geo = {f"{field}.geo": {"lat": coord[0], "lon": coord[1]}}
        self._filter.append(
            {
                "geo_distance": {
                    "distance": f"{coord[2]}km",
                    **self._geo,
                }
            }
        )

        return self

    def build(
        self,
        *,
        limit: int,
        cursor: list[Any] | None = None,
    ) -> dict[str, Any]:
        body = {"size": limit, "query": self._query(), "sort": self._sort()}
        if cursor:
            body["search_after"] = cursor

        return body

    def execute(
        self,
        *,
        limit: int,
        cursor: list[Any] | None = None,
    ) -> dict[str, Any]:
        body = self.build(limit=limit, cursor=cursor)
        response = self.using.search(index=self.index, body=body)

        hits: list[dict[str, Any]] = response["hits"]["hits"]
        return {
            "Items": [
                {
                    "id": hit["_source"]["id"],
                    "score": hit.get("_score"),
                    "source": hit["_source"],
                }
                for hit in hits
            ],
            "Cursor": hits[-1]["sort"] if len(hits) == limit else None,
        }
