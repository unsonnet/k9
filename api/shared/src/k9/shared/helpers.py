from datetime import datetime, timezone
from typing import overload

# ──── Datetime ────────────────────────────────────────────────────────────────────────


def now() -> datetime:
    return datetime.now(timezone.utc)


@overload
def dt(value: datetime) -> datetime: ...
@overload
def dt(value: str, iso: bool = True) -> datetime: ...
@overload
def dt(value: None, iso: bool = True) -> None: ...
def dt(value: datetime | str | None, iso: bool = True) -> datetime | None:
    match value:
        case datetime() as dt:
            return dt.astimezone(timezone.utc)
        case str() as s:
            if iso:
                return datetime.fromisoformat(s).astimezone(timezone.utc)
            return datetime.strptime(s, "%Y-%m-%d %H:%M:%S %Z").astimezone(timezone.utc)
        case None:
            return None


# ──── Query ───────────────────────────────────────────────────────────────────────────


def sanitize_query(q: str) -> str | None:
    return q.replace("\\", "\\\\").replace('"', '\\"') if (q := q.strip()) else None
