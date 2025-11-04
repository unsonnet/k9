#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Mapping, Sequence
from uuid import UUID

from pydantic import BaseModel
from pydantic.types import NonNegativeInt, PositiveInt

from .common import NonEmptyStr
from .product import Image, ProductName


# ──────────────────────────────────────────────────────────────────────────────
# Filters & Request Models
# ──────────────────────────────────────────────────────────────────────────────
class DimensionRange(BaseModel):
    unit: NonEmptyStr
    min: int | None = None
    max: int | None = None


class CurrencyRange(BaseModel):
    unit: NonEmptyStr
    min: int | None = None
    max: int | None = None


class VendorFilter(BaseModel):
    sku: NonEmptyStr | None = None
    store: Sequence[NonEmptyStr] | None = None
    name: NonEmptyStr | None = None
    price: CurrencyRange | None = None
    discontinued: bool | None = None


class FormatFilter(BaseModel):
    aspect: NonEmptyStr | None = None
    length: DimensionRange | None = None
    width: DimensionRange | None = None
    thickness: DimensionRange | None = None


class NameFilter(BaseModel):
    brand: NonEmptyStr | None = None
    series: NonEmptyStr | None = None
    model: NonEmptyStr | None = None


class SearchRequest(BaseModel):
    name: NameFilter | None = None
    category: Mapping[str, Sequence[str]] | None = None
    format: FormatFilter | None = None
    vendor: VendorFilter | None = None
    colors: Sequence[str] | None = None
    references: Sequence[UUID] | None = None


class SearchParams(BaseModel):
    limit: PositiveInt | None = None
    nextToken: NonEmptyStr | None = None
    partial: bool | None = None


class SearchOKBody(BaseModel):
    total: NonNegativeInt
    results: Sequence["SearchProductSummary"]
    nextToken: NonEmptyStr | None = None


# ──────────────────────────────────────────────────────────────────────────────
# Provider-side models
# ──────────────────────────────────────────────────────────────────────────────
class SearchHit(BaseModel):
    id: UUID
    score: int


class SearchResult(BaseModel):
    total: NonNegativeInt
    hits: Sequence[SearchHit]
    nextToken: NonEmptyStr | None = None


class SearchProductSummary(BaseModel):
    id: UUID
    name: ProductName
    image: Image
    match: int
