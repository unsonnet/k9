import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from shared.errors import DomainInvariantViolation
from shared.helpers import sanitize_query

__all__ = [
    "Bool",
    "Term",
    "Prefix",
    "Text",
    "Near",
    "Range",
    "Exclude",
    "AllOf",
    "AnyOf",
    "Query",
]

type _Clause = dict[str, Any]

_SUBRESOURCE = re.compile(r"(?:\$[^.]+\.)*\$[^.]+(?=\.)")


def nested_path(field: str) -> str | None:
    """Subresources (`$name`) are indexed as nested objects."""
    return match.group() if (match := _SUBRESOURCE.match(field)) else None


@dataclass(slots=True)
class Bool:
    """Accumulator for the clauses of a bool query."""

    scoped: bool = True  # wrap subresource fields in nested queries
    should: list[_Clause] = field(default_factory=list)
    filter: list[_Clause] = field(default_factory=list)
    geo: _Clause | None = None  # origin used to sort by distance

    def scope(self, field: str, clause: _Clause, **options: Any) -> _Clause:
        if self.scoped and (path := nested_path(field)):
            return {"nested": {"path": path, "query": clause, **options}}
        return clause


def _match(query: str, fields: list[str], type: str, **options: Any) -> _Clause:
    return {"multi_match": {"query": query, "fields": fields, "type": type, **options}}


def _filters(queries: Sequence["Query"], scoped: bool) -> list[_Clause]:
    acc = Bool(scoped)
    for query in queries:
        query.apply(acc)
    return acc.filter


def _all(filters: list[_Clause]) -> _Clause:
    return filters[0] if len(filters) == 1 else {"bool": {"filter": filters}}


def _flatten(args: Iterable["Query | Iterable[Query]"]) -> tuple["Query", ...]:
    """Accept queries unpacked or as iterables (e.g. generators)."""
    return tuple(q for a in args for q in (a if isinstance(a, Iterable) else (a,)))


@dataclass(slots=True, init=False)
class Term:
    field: str
    options: tuple[str, ...]

    def __init__(self, field: str, *options: str) -> None:
        self.field = field
        self.options = options

    def apply(self, acc: Bool) -> None:
        if self.options:
            clause = {"terms": {self.field: self.options}}
            acc.filter.append(acc.scope(self.field, clause))


@dataclass(frozen=True, slots=True)
class Prefix:
    field: str
    value: str

    def apply(self, acc: Bool) -> None:
        if self.value:
            prefix = {"value": self.value, "case_insensitive": True}
            clause = {"prefix": {self.field: prefix}}
            acc.filter.append(acc.scope(self.field, clause))


@dataclass(frozen=True, slots=True)
class Text:
    """Ranked text match: exact words, search-as-you-type, then typos."""

    field: str
    query: str

    def apply(self, acc: Bool) -> None:
        if not (query := sanitize_query(self.query)):
            return
        f = self.field
        clauses = [
            _match(query, [f"{f}^5", f"{f}.wdg^4"], "best_fields", operator="and"),
            _match(
                query,
                [f"{f}.sat", f"{f}.sat._2gram", f"{f}.sat._3gram"],
                "bool_prefix",
                boost=2,
            ),
            _match(
                query,
                [f"{f}^2", f"{f}.wdg"],
                "best_fields",
                operator="and",
                fuzziness="AUTO",
                prefix_length=1,
                max_expansions=25,
                boost=0.4,
            ),
        ]
        acc.should.extend(acc.scope(f, c, score_mode="max") for c in clauses)


@dataclass(frozen=True, slots=True)
class Near:
    """Restrict to a radius in km and sort by distance."""

    field: str
    coord: tuple[Decimal, Decimal, int]

    def apply(self, acc: Bool) -> None:
        if acc.geo is not None:
            raise DomainInvariantViolation("Only one Near query is supported")
        lat, lon, radius = self.coord
        acc.geo = {self.field: {"lat": lat, "lon": lon}}
        acc.filter.append(
            acc.scope(
                self.field, {"geo_distance": {"distance": f"{radius}km", **acc.geo}}
            )
        )


@dataclass(frozen=True, slots=True)
class Range:
    field: str
    gte: Decimal | None
    lte: Decimal | None
    unknown: bool = False  # also match documents lacking the field

    def apply(self, acc: Bool) -> None:
        bounds = {"gte": self.gte, "lte": self.lte}
        if not (bounds := {op: v for op, v in bounds.items() if v is not None}):
            return
        clause: _Clause = {"range": {self.field: bounds}}
        if self.unknown:
            absent = {"bool": {"must_not": {"exists": {"field": self.field}}}}
            clause = {"bool": {"should": [clause, absent], "minimum_should_match": 1}}
        acc.filter.append(acc.scope(self.field, clause))


@dataclass(slots=True, init=False)
class Exclude:
    ids: tuple[str, ...]

    def __init__(self, *ids: str) -> None:
        self.ids = ids

    def apply(self, acc: Bool) -> None:
        if self.ids:
            acc.filter.append({"bool": {"must_not": {"ids": {"values": self.ids}}}})


@dataclass(slots=True, init=False)
class AllOf:
    """Satisfy all queries; `nest` requires those under one subresource to match the same object."""

    queries: tuple["Query", ...]
    nest: bool

    def __init__(self, *queries: "Query | Iterable[Query]", nest: bool = False) -> None:
        self.queries = _flatten(queries)
        self.nest = nest

    def apply(self, acc: Bool) -> None:
        filters = _filters(self.queries, acc.scoped)
        if not self.nest:
            acc.filter.extend(filters)
            return
        groups: dict[str, list[_Clause]] = {}
        for clause in filters:
            if "nested" in clause:
                nested = clause["nested"]
                groups.setdefault(nested["path"], []).append(nested["query"])
            else:
                acc.filter.append(clause)
        for path, queries in groups.items():
            acc.filter.append({"nested": {"path": path, "query": _all(queries)}})


@dataclass(slots=True, init=False)
class AnyOf:
    """Match any query; one that adds no constraint matches everything."""

    queries: tuple["Query", ...]

    def __init__(self, *queries: "Query | Iterable[Query]") -> None:
        self.queries = _flatten(queries)

    def apply(self, acc: Bool) -> None:
        options = [_filters([query], acc.scoped) for query in self.queries]
        if options and all(options):
            should = [_all(option) for option in options]
            acc.filter.append({"bool": {"should": should, "minimum_should_match": 1}})


type Query = Term | Prefix | Text | Near | Range | Exclude | AllOf | AnyOf
