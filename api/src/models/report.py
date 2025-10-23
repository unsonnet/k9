#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from datetime import datetime
from typing import Sequence
from uuid import UUID

from pydantic import BaseModel
from pydantic.types import NonNegativeInt, PositiveInt

from .common import NonEmptyStr
from .product import Product, ProductSummary


# ──────────────────────────────────────────────────────────────────────────────
# Report Models
# ──────────────────────────────────────────────────────────────────────────────
class ReportSummary(BaseModel):
    id: UUID
    author: UUID
    title: NonEmptyStr
    date: datetime
    reference: ProductSummary


class StoredReportSummary(BaseModel):
    id: UUID
    author: UUID
    title: NonEmptyStr
    createdAt: datetime
    updatedAt: datetime | None = None
    referenceId: UUID


class Report(BaseModel):
    id: UUID
    author: UUID
    title: NonEmptyStr
    date: datetime
    reference: Product
    favorites: Sequence[Product] = ()


class StoredReport(BaseModel):
    id: UUID
    author: UUID
    title: NonEmptyStr
    createdAt: datetime
    updatedAt: datetime | None = None
    referenceId: UUID
    favoriteIds: Sequence[UUID] = ()


# ──────────────────────────────────────────────────────────────────────────────
# Requests & Params
# ──────────────────────────────────────────────────────────────────────────────
class ListReportsParams(BaseModel):
    limit: PositiveInt | None = None
    nextToken: NonEmptyStr | None = None
    everyone: bool | None = None


class ListReportsOKBody(BaseModel):
    total: NonNegativeInt
    reports: Sequence[ReportSummary]
    nextToken: NonEmptyStr | None = None


class CreateReportRequest(BaseModel):
    title: NonEmptyStr
    reference: UUID


class UpdateReportRequest(BaseModel):
    title: NonEmptyStr | None = None
    reference: UUID | None = None
