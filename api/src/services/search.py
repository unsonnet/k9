#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import NoReturn

from utils.http import Forbidden, InternalServerError, NotFound, OK, Unauthorized

from models.auth import AuthContext
from models.search import (
    SearchOKBody,
    SearchParams,
    SearchProductSummary,
    SearchRequest,
)

from utils.errors import (
    DomainForbidden,
    DomainInvariantViolation,
    DomainNotFound,
    DomainUnauthorized,
)

from providers.search import ProductSummaryProvider, SearchProvider


# ──────────────────────────────────────────────────────────────────────────────
# Search Service
# ──────────────────────────────────────────────────────────────────────────────
class SearchService:
    """
    API-facing orchestrator for search operations.
    Delegates to providers, maps domain errors to HTTP responses,
    and composes ProductSummaries per hit.
    """

    provider: SearchProvider
    products: ProductSummaryProvider

    def __init__(self):
        from providers.search import _NoopProductSummaryProvider, _NoopSearchProvider

        self.provider = _NoopSearchProvider()
        self.products = _NoopProductSummaryProvider()

    # ─────────── Helpers ───────────
    @staticmethod
    def _handle_error(e: Exception, msg: str = "Internal error") -> NoReturn:
        mapping = {
            DomainUnauthorized: lambda: Unauthorized("Not authorized."),
            DomainForbidden: lambda: Forbidden("Forbidden."),
            DomainNotFound: lambda: NotFound(msg),
            DomainInvariantViolation: lambda: InternalServerError(str(e)),
        }
        raise mapping.get(type(e), lambda: InternalServerError(str(e)))()

    # ─────────── Endpoints ───────────
    # POST /search → 200 | 400 | 401 | 403 | 404 | 500
    def search(
        self, ctx: AuthContext, params: SearchParams, payload: SearchRequest
    ) -> OK[SearchOKBody]:
        try:
            result = self.provider.search(
                ctx,
                query=payload,
                limit=params.limit,
                next_token=params.nextToken,
                partial=params.partial,
            )
            summaries: list[SearchProductSummary] = []
            for hit in result.hits:
                summary = self.products.get_summary(ctx, pid=hit.id)
                summaries.append(
                    SearchProductSummary(
                        id=summary.id,
                        name=summary.name,
                        image=summary.image,
                        match=hit.score,
                    )
                )
            body = SearchOKBody(
                total=result.total, results=summaries, nextToken=result.nextToken
            )
            return OK(body)
        except Exception as e:
            self._handle_error(e, "Referenced products not found.")
