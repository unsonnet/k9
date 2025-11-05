#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Shared model utilities and value objects."""

from __future__ import annotations

from typing import Optional
from pydantic import ConfigDict
from .base import DomainModel
from .types import NonEmptyStr

# ──────────────────────────────────────────────────────────────────────────────
# Common Value Objects
# ──────────────────────────────────────────────────────────────────────────────


class Dimension(DomainModel):
    """Physical dimension with value and unit."""

    model_config = ConfigDict(frozen=True)

    value: int
    unit: NonEmptyStr


class Currency(DomainModel):
    """Monetary value with amount and currency unit."""

    model_config = ConfigDict(frozen=True)

    value: int
    unit: NonEmptyStr


class Name(DomainModel):
    """Product naming schema with optional brand, series, and model."""

    model_config = ConfigDict(frozen=True)

    brand: Optional[NonEmptyStr] = None
    series: Optional[NonEmptyStr] = None
    model: Optional[NonEmptyStr] = None
