from __future__ import annotations

import re
import unicodedata
from datetime import datetime
from typing import Annotated, Literal, NewType

from pydantic import AfterValidator, BaseModel, StringConstraints

# ──── Credentials ─────────────────────────────────────────────────────────────────────


def _normalize_name(name: str) -> str:
    name = unicodedata.normalize("NFKC", name)
    return re.sub(r"\s+", " ", name.strip()).casefold()


Name = Annotated[
    NewType("Name", str),
    AfterValidator(_normalize_name),
    StringConstraints(min_length=1, max_length=1024),
]


Password = Annotated[
    NewType("Password", str),
    StringConstraints(
        min_length=8,
        max_length=256,
        pattern=re.compile(
            r"\A(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[!@#$%^&*()_=+\[\]{}:,.?\-])\S+\Z"
        ),
    ),
]


# ──── Identity ────────────────────────────────────────────────────────────────────────


UserID = Annotated[
    NewType("UserID", str),
    StringConstraints(pattern=r"\A[a-z]{3}\d{3}\z"),
]

type Role = Literal["admin", "user"]


class Caller(BaseModel):
    id: UserID
    role: Role
    name: Name
    token: str

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"


# ──── Resources ───────────────────────────────────────────────────────────────────────


def _validate_datetime(value: str) -> str:
    dt = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    return dt.isoformat(timespec="seconds") + "Z"


ResourceID = Annotated[
    NewType("ResourceID", str),
    StringConstraints(pattern=r"\A\d{3}-\d{3}-\d{3}\z"),
]

SubresourceID = Annotated[
    NewType("SubresourceID", str),
    StringConstraints(pattern=r"\A\d{4}\z"),
]

DateID = Annotated[
    NewType("DateID", str),
    AfterValidator(_validate_datetime),
]
