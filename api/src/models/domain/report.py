#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Report domain models - Business entities for report management."""

from __future__ import annotations

from datetime import datetime
from typing import Sequence
from uuid import UUID

from ..shared.base import DomainModel, StorageModel, TimeStamped
from ..shared.types import NonEmptyStr
from .product import Product, ProductSummary

# ──────────────────────────────────────────────────────────────────────────────
# Domain Entities
# ──────────────────────────────────────────────────────────────────────────────


class ReportSummary(DomainModel):
    """Report summary for listings and references."""

    id: UUID
    author_id: UUID
    title: NonEmptyStr
    created_at: datetime
    reference_product: ProductSummary


class Report(DomainModel):
    """Complete report with reference and favorites."""

    id: UUID
    author_id: UUID
    title: NonEmptyStr
    created_at: datetime
    reference_product: Product
    favorite_products: Sequence[Product] = ()


class ReportEntity(StorageModel, TimeStamped):
    """Report entity with persistence metadata."""

    id: UUID
    author_id: UUID
    title: NonEmptyStr
    reference_product_id: UUID
    favorite_product_ids: Sequence[UUID] = ()
