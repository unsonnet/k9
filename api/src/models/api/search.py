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
    min: Optional[int] = None
    max: Optional[int] = None


class CurrencyRangeFilter(ApiModel):
    """Currency range filter for vendor pricing."""

    unit: NonEmptyStr
    min: Optional[int] = None
    max: Optional[int] = None


class VendorFilter(ApiModel):
    """Vendor-specific search filters."""

    sku: Optional[NonEmptyStr] = None
    store: Optional[Sequence[NonEmptyStr]] = None
    name: Optional[NonEmptyStr] = None
    price: Optional[CurrencyRangeFilter] = None
    discontinued: Optional[bool] = None


class FormatFilter(ApiModel):
    """Format-specific search filters."""

    aspect: Optional[NonEmptyStr] = None
    length: Optional[DimensionRangeFilter] = None
    width: Optional[DimensionRangeFilter] = None
    thickness: Optional[DimensionRangeFilter] = None


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

    name: Optional[NameFilter] = None
    category: Optional[Mapping[str, Sequence[str]]] = None
    format: Optional[FormatFilter] = None
    vendor: Optional[VendorFilter] = None
    color: Optional[Sequence[str]] = None
    reference: Optional[Sequence[UUID]] = None


class SearchParams(ApiModel):
    """Search request parameters for pagination and options."""

    limit: Optional[PositiveInt] = None
    nextToken: Optional[NonEmptyStr] = None
    partial: Optional[bool] = None


# ──────────────────────────────────────────────────────────────────────────────
# Response Models
# ──────────────────────────────────────────────────────────────────────────────


class SearchResultItem(ApiModel):
    """Individual search result with match score."""

    id: UUID
    name: Name
    image: str
    match: int


class SearchResponse(ApiModel):
    """Search results response with pagination."""

    total: NonNegativeInt
    results: Sequence[SearchResultItem]
    nextToken: Optional[NonEmptyStr] = None
