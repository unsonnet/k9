#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Report API models - Request/Response DTOs for report endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Sequence
from uuid import UUID
from pydantic.types import NonNegativeInt, PositiveInt

from ..shared.base import ApiModel
from ..shared.types import NonEmptyStr

# ──────────────────────────────────────────────────────────────────────────────
# Request Models
# ──────────────────────────────────────────────────────────────────────────────


class ListReportsRequest(ApiModel):
    """List reports with pagination and filtering."""

    limit: PositiveInt | None = None
    nextToken: NonEmptyStr | None = None
    everyone: bool | None = None


class CreateReportRequest(ApiModel):
    """Create new report request."""

    title: NonEmptyStr
    reference: UUID


class UpdateReportRequest(ApiModel):
    """Update report request - all fields optional for PATCH."""

    title: NonEmptyStr | None = None
    reference: UUID | None = None


# ──────────────────────────────────────────────────────────────────────────────
# Response Models
# ──────────────────────────────────────────────────────────────────────────────


class ReportSummaryResponse(ApiModel):
    """Report summary for listings."""

    id: UUID
    author: UUID
    title: NonEmptyStr
    date: datetime
    reference: dict  # ProductSummary as dict for API


class ReportResponse(ApiModel):
    """Complete report information for API responses."""

    id: UUID
    author: UUID
    title: NonEmptyStr
    date: datetime
    reference: dict  # Product as dict for API
    favorites: Sequence[dict] = ()  # Products as dicts


class ListReportsResponse(ApiModel):
    """Paginated list of reports response."""

    total: NonNegativeInt
    reports: Sequence[ReportSummaryResponse]
    nextToken: NonEmptyStr | None = None
