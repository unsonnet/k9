from datetime import datetime, timezone
from typing import overload


@overload
def dt(value: datetime) -> datetime: ...
@overload
def dt(value: None) -> None: ...
def dt(value: datetime | None) -> datetime | None:
    match value:
        case datetime() as dt:
            return dt.astimezone(timezone.utc)
        case None:
            return None
