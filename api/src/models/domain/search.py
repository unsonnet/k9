#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Search domain models - Business entities for search operations."""

from __future__ import annotations

from typing import Sequence
from uuid import UUID
from pydantic.types import NonNegativeInt

from ..shared.base import DomainModel
from ..shared.types import NonEmptyStr
from ..shared.values import Name
from .product import ImageInfo

# ──────────────────────────────────────────────────────────────────────────────
# Search Result Models
# ──────────────────────────────────────────────────────────────────────────────


class SearchHit(DomainModel):
    """Individual search hit with relevance score."""

    id: UUID
    score: int


class ProductSearchResult(DomainModel):
    """Enhanced product search result with full details."""

    id: UUID
    name: Name
    image: ImageInfo
    match_score: int


class SearchResults(DomainModel):
    """Complete search results with product details."""

    total: NonNegativeInt
    products: Sequence[ProductSearchResult]
    next_token: NonEmptyStr | None = None
