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
    next_token: NonEmptyStr | None = None
    include_all_users: bool | None = None


class CreateReportRequest(ApiModel):
    """Create new report request."""

    title: NonEmptyStr
    reference_product_id: UUID


class UpdateReportRequest(ApiModel):
    """Update report request - all fields optional for PATCH."""

    title: NonEmptyStr | None = None
    reference_product_id: UUID | None = None


# ──────────────────────────────────────────────────────────────────────────────
# Response Models
# ──────────────────────────────────────────────────────────────────────────────


class ReportSummaryResponse(ApiModel):
    """Report summary for listings."""

    id: UUID
    author_id: UUID
    title: NonEmptyStr
    created_at: datetime
    reference_product: dict  # ProductSummary as dict for API


class ReportResponse(ApiModel):
    """Complete report information for API responses."""

    id: UUID
    author_id: UUID
    title: NonEmptyStr
    created_at: datetime
    reference_product: dict  # Product as dict for API
    favorite_products: Sequence[dict] = ()  # Products as dicts


class ListReportsResponse(ApiModel):
    """Paginated list of reports response."""

    total: NonNegativeInt
    reports: Sequence[ReportSummaryResponse]
    next_token: NonEmptyStr | None = None
