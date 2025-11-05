#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Shared type definitions and constraints used across API and domain layers."""

from __future__ import annotations

from typing import Annotated, Mapping
from pydantic import StringConstraints

# ──────────────────────────────────────────────────────────────────────────────
# String Type Constraints
# ──────────────────────────────────────────────────────────────────────────────

NonEmptyStr = Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)]
"""Non-empty string with whitespace stripped."""

TokenStr = Annotated[str, StringConstraints(min_length=16, strip_whitespace=True)]
"""Security token string (min 16 chars)."""

PasswordStr = Annotated[str, StringConstraints(min_length=8, strip_whitespace=False)]
"""Password string (min 8 chars, preserves whitespace)."""

SessionStr = Annotated[str, StringConstraints(min_length=10, strip_whitespace=True)]
"""Session identifier string (min 10 chars)."""

UsernameStr = Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)]
"""Username string (non-empty, trimmed)."""

RoleStr = Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)]
"""User role string (non-empty, trimmed)."""

PrefValueStr = Annotated[str, StringConstraints(min_length=0, strip_whitespace=False)]
"""Preference value string (preserves whitespace, can be empty)."""

# E.164 phone number: leading +, country code 1-9, 7–14 additional digits
PhoneStr = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        pattern=r"^\+[1-9][0-9]{7,14}$",
    ),
]
"""E.164 format phone number (+country_code followed by 7-14 digits)."""

# ──────────────────────────────────────────────────────────────────────────────
# Mapping Types
# ──────────────────────────────────────────────────────────────────────────────

CategoryMap = Mapping[str, NonEmptyStr]
"""Category mapping for products (key -> non-empty value)."""

PreferencesMap = Mapping[str, PrefValueStr]
"""User preferences mapping (key -> preference value)."""
