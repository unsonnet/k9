#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Base model classes and shared infrastructure."""

from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel

# ──────────────────────────────────────────────────────────────────────────────
# Base Model Classes
# ──────────────────────────────────────────────────────────────────────────────


class TimeStamped(BaseModel):
    """Base model with creation and update timestamps."""

    created_at: datetime
    updated_at: datetime | None = None


class ApiModel(BaseModel):
    """Base class for API request/response models."""

    model_config = {"frozen": True, "extra": "forbid"}


class DomainModel(BaseModel):
    """Base class for domain entities and value objects."""

    model_config = {"frozen": True, "extra": "forbid"}


class StorageModel(BaseModel):
    """Base class for storage/persistence models."""

    model_config = {"extra": "forbid"}
