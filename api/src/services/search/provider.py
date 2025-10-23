#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

# ──────────────────────────────────────────────────────────────────────────────
from models.common import AuthContext
from models.product import ProductSummary
from models.search import (
    SearchRequest,
    SearchResult,
)


# ──────────────────────────────────────────────────────────────────────────────
# Provider Interfaces
# ──────────────────────────────────────────────────────────────────────────────
class SearchProvider(ABC):
    """Backend contract for product search semantics."""

    @abstractmethod
    def search(
        self,
        ctx: AuthContext,
        *,
        query: SearchRequest,
        limit: int | None,
        next_token: str | None,
        partial: bool | None,
    ) -> SearchResult: ...


class ProductSummaryProvider(ABC):
    """Minimal resolver for building ProductSummary from a product id."""

    @abstractmethod
    def get_summary(self, ctx: AuthContext, *, pid: UUID) -> ProductSummary: ...


# Default no-op providers used by service constructors unless overridden
class _NoopSearchProvider(SearchProvider):  # pragma: no cover - placeholder
    def search(self, *_, **__) -> SearchResult:  # type: ignore[override]
        raise NotImplementedError("SearchProvider not configured")


class _NoopProductSummaryProvider(
    ProductSummaryProvider
):  # pragma: no cover - placeholder
    def get_summary(self, *_, **__) -> ProductSummary:  # type: ignore[override]
        raise NotImplementedError("ProductSummaryProvider not configured")
