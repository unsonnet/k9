#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from models.domain.auth import AuthContext
from models.domain.product import ProductSummary
from models.api.search import SearchRequest
from models.domain.search import SearchResults


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
    ) -> SearchResults: ...


class ProductSummaryProvider(ABC):
    """Minimal resolver for building ProductSummary from a product id."""

    @abstractmethod
    def get_summary(self, ctx: AuthContext, *, pid: UUID) -> ProductSummary: ...


# Default no-op providers used by service constructors unless overridden
class NoopSearchProvider(SearchProvider):  # pragma: no cover - placeholder
    def search(self, *_, **__) -> SearchResult:  # type: ignore[override]
        raise NotImplementedError("SearchProvider not configured")


class NoopProductSummaryProvider(
    ProductSummaryProvider
):  # pragma: no cover - placeholder
    def get_summary(self, *_, **__) -> ProductSummary:  # type: ignore[override]
        raise NotImplementedError("ProductSummaryProvider not configured")
