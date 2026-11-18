from dataclasses import dataclass

__all__ = [
    "EventSpec",
    "GrantSpec",
    "RouteSpec",
]


@dataclass(frozen=True)
class GrantSpec:
    effect: str = "allow"
    actions: tuple[str, ...] = ()
    resources: tuple[str, ...] = ()


@dataclass(frozen=True)
class RouteSpec:
    method: str
    rule: str
    auth_required: bool
    operation_id: str | None = None
    summary: str | None = None
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class EventSpec:
    source: str
    event: str
    rule: str
