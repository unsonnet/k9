#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Search API models - Request/Response DTOs for search endpoints."""

from __future__ import annotations

from typing import Mapping, Optional, Sequence
from uuid import UUID
from pydantic.types import NonNegativeInt, PositiveInt

from ..shared.base import ApiModel
from ..shared.types import NonEmptyStr
from ..shared.values import Name

# ──────────────────────────────────────────────────────────────────────────────
# Filter Models
# ──────────────────────────────────────────────────────────────────────────────


class DimensionRangeFilter(ApiModel):
    """Dimension range filter for product formats."""

    unit: NonEmptyStr
    min_value: Optional[int] = None
    max_value: Optional[int] = None


class CurrencyRangeFilter(ApiModel):
    """Currency range filter for vendor pricing."""

    unit: NonEmptyStr
    min_value: Optional[int] = None
    max_value: Optional[int] = None


class VendorFilter(ApiModel):
    """Vendor-specific search filters."""

    sku: Optional[NonEmptyStr] = None
    stores: Optional[Sequence[NonEmptyStr]] = None
    name: Optional[NonEmptyStr] = None
    price_range: Optional[CurrencyRangeFilter] = None
    discontinued: Optional[bool] = None


class FormatFilter(ApiModel):
    """Format-specific search filters."""

    aspect: Optional[NonEmptyStr] = None
    length_range: Optional[DimensionRangeFilter] = None
    width_range: Optional[DimensionRangeFilter] = None
    thickness_range: Optional[DimensionRangeFilter] = None


class NameFilter(ApiModel):
    """Product name search filters."""

    brand: Optional[NonEmptyStr] = None
    series: Optional[NonEmptyStr] = None
    model: Optional[NonEmptyStr] = None


# ──────────────────────────────────────────────────────────────────────────────
# Request Models
# ──────────────────────────────────────────────────────────────────────────────


class SearchRequest(ApiModel):
    """Product search request with comprehensive filters."""

    name_filter: Optional[NameFilter] = None
    category_filter: Optional[Mapping[str, Sequence[str]]] = None
    format_filter: Optional[FormatFilter] = None
    vendor_filter: Optional[VendorFilter] = None
    colors: Optional[Sequence[str]] = None
    reference_ids: Optional[Sequence[UUID]] = None


class SearchParams(ApiModel):
    """Search request parameters for pagination and options."""

    limit: Optional[PositiveInt] = None
    next_token: Optional[NonEmptyStr] = None
    include_partial_matches: Optional[bool] = None


# ──────────────────────────────────────────────────────────────────────────────
# Response Models
# ──────────────────────────────────────────────────────────────────────────────


class SearchResultItem(ApiModel):
    """Individual search result with match score."""

    id: UUID
    name: Name
    image_url: str
    match_score: int


class SearchResponse(ApiModel):
    """Search results response with pagination."""

    total: NonNegativeInt
    results: Sequence[SearchResultItem]
    next_token: Optional[NonEmptyStr] = None
