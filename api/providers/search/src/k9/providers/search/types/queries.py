import re
from dataclasses import dataclass, field
from typing import Any, Final, Protocol

__all__ = [
    "Bool",
    "Clause",
    "Query",
]


_SUBRESOURCE_RE: Final = re.compile(r"(?:\$[^.]+\.)*\$[^.]+(?=\.)")

type Clause = dict[str, Any]


@dataclass(slots=True)
class Bool:
    scoped: bool = True
    should: list[Clause] = field(default_factory=list)
    filter: list[Clause] = field(default_factory=list)
    geo: Clause | None = None

    def scope(self, field: str, clause: Clause, **options: Any) -> Clause:
        if self.scoped and (path := self.nested_path(field)):
            return {"nested": {"path": path, "query": clause, **options}}
        return clause

    @property
    def query(self) -> Clause:
        clauses = {}
        if self.should:
            clauses["should"] = self.should
            clauses["minimum_should_match"] = 1
        if self.filter:
            clauses["filter"] = self.filter
        return {"bool": clauses} if clauses else {"match_all": {}}

    @property
    def sort(self) -> list[Clause]:
        sort = []
        if self.should:
            sort.append({"_score": {"order": "desc"}})
        if self.geo:
            geo = {
                "_geo_distance": {
                    **self.geo,
                    "order": "asc",
                    "unit": "km",
                    "mode": "min",
                    "distance_type": "arc",
                }
            }
            if path := self.nested_path(next(iter(self.geo))):
                geo["_geo_distance"]["nested"] = {"path": path}
            sort.append(geo)
        sort.append({"id": {"order": "asc"}})
        return sort

    @staticmethod
    def nested_path(field: str) -> str | None:
        return match.group() if (match := _SUBRESOURCE_RE.match(field)) else None


class Query(Protocol):
    def apply(self, acc: Bool) -> None: ...
