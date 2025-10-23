#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Annotated, Mapping
from datetime import datetime

from pydantic import BaseModel, StringConstraints

# ──────────────────────────────────────────────────────────────────────────────
# Strong type aliases (shared)
# ──────────────────────────────────────────────────────────────────────────────
NonEmptyStr = Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)]
TokenStr = Annotated[str, StringConstraints(min_length=16, strip_whitespace=True)]
PasswordStr = Annotated[str, StringConstraints(min_length=8, strip_whitespace=False)]
SessionStr = Annotated[str, StringConstraints(min_length=10, strip_whitespace=True)]
UsernameStr = Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)]
RoleStr = Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)]
PrefValueStr = Annotated[str, StringConstraints(min_length=0, strip_whitespace=False)]

# Common mapping types
CategoryMap = Mapping[str, NonEmptyStr]


# ──────────────────────────────────────────────────────────────────────────────
# Base Models
# ──────────────────────────────────────────────────────────────────────────────
class TimeStamped(BaseModel):
    createdAt: datetime
    updatedAt: datetime | None = None
