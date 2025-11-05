#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations
from datetime import datetime, timezone
from typing import NoReturn
from uuid import UUID

from utils.http import (
    Created,
    InternalServerError,
    NoContent,
    NotFound,
    OK,
    Forbidden,
    Unauthorized,
)

from models.domain.auth import AuthContext
from models.api.report import (
    CreateReportRequest,
    ListReportsRequest,
    ListReportsResponse,
    ReportSummaryResponse,
    UpdateReportRequest,
)
from models.domain.report import (
    Report,
    ReportSummary,
    ReportEntity,
)

from utils.errors import (
    DomainForbidden,
    DomainInvariantViolation,
    DomainNotFound,
    DomainUnauthorized,
)

from providers.report import ProductResolver, ReportDBProvider, UserResolver


# ──────────────────────────────────────────────────────────────────────────────
# Report Service
# ──────────────────────────────────────────────────────────────────────────────
class ReportService:
    """
    API-facing orchestrator for report management.
    Mirrors provider contract and matches user/product/auth service patterns.
    """

    provider: ReportDBProvider
    products: ProductResolver
    users: UserResolver

    def __init__(self):
        from providers.report import (
            NoopProductResolver,
            NoopReportDBProvider,
            NoopUserResolver,
        )

        self.provider = NoopReportDBProvider()
        self.products = NoopProductResolver()
        self.users = NoopUserResolver()

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

    @staticmethod
    def _touch(r: ReportEntity, **updates) -> ReportEntity:
        return r.model_copy(update={**updates, "updatedAt": datetime.now(timezone.utc)})

    def _public_summary_to_api(
        self, ctx: AuthContext, s: ReportSummary
    ) -> ReportSummaryResponse:
        return ReportSummaryResponse(
            id=s.id,
            author=s.author_id,
            title=s.title,
            date=s.created_at,
            reference=s.reference_product.model_dump(),
        )

    def _public_report(self, ctx: AuthContext, r: ReportEntity) -> Report:
        ref = self.products.get_product(ctx=ctx, pid=r.reference_product_id)
        favs = [
            self.products.get_product(ctx=ctx, pid=fid)
            for fid in r.favorite_product_ids
        ]
        return Report(
            id=r.id,
            author_id=r.author_id,
            title=r.title,
            created_at=r.created_at,
            reference_product=ref,
            favorite_products=favs,
        )

    # ─────────── Endpoints ───────────
    # GET /report → 200 | 401 | 403 | 500
    def list_reports(
        self, ctx: AuthContext, params: ListReportsRequest
    ) -> OK[ListReportsResponse]:
        try:
            res = self.provider.list_reports(
                ctx,
                limit=params.limit,
                next_token=params.next_token,
                everyone=params.include_all_users,
            )
            body = ListReportsResponse(
                total=res.total,
                reports=[self._public_summary_to_api(ctx, s) for s in res.reports],
                next_token=res.nextToken,
            )
            return OK(body)
        except Exception as e:
            self._handle_error(e, "Failed to list reports.")

    # POST /report → 201 | 400 | 401 | 403 | 404 | 500
    def create_report(
        self, ctx: AuthContext, payload: CreateReportRequest
    ) -> Created[Report]:
        try:
            rep = self.provider.post_report(
                ctx,
                author=self.users.get_user_id(ctx),
                title=payload.title,
                reference=payload.reference,
            )
            return Created(self._public_report(ctx, rep))
        except Exception as e:
            self._handle_error(e, "Failed to create report.")

    # GET /report/{rid} → 200 | 401 | 403 | 404 | 500
    def get_report(self, ctx: AuthContext, rid: UUID) -> OK[Report]:
        try:
            stored = self.provider.get_report(ctx, rid=rid)
            return OK(self._public_report(ctx, stored))
        except Exception as e:
            self._handle_error(e, "Report not found.")

    # PATCH /report/{rid} → 200 | 400 | 401 | 403 | 404 | 500
    def update_report(
        self, ctx: AuthContext, rid: UUID, payload: UpdateReportRequest
    ) -> OK[Report]:
        try:
            rep = self.provider.get_report(ctx, rid=rid)
            title = payload.title or rep.title
            reference_id = payload.reference or rep.reference_product_id
            updated = self._touch(rep, title=title, referenceId=reference_id)
            stored = self.provider.put_report(ctx, report=updated)
            return OK(self._public_report(ctx, stored))
        except Exception as e:
            self._handle_error(e, "Failed to update report.")

    # DELETE /report/{rid} → 204 | 401 | 403 | 404 | 500
    def delete_report(self, ctx: AuthContext, rid: UUID) -> NoContent:
        try:
            self.provider.delete_report(ctx, rid=rid)
            return NoContent()
        except Exception as e:
            self._handle_error(e, "Report not found.")

    # PUT /report/{rid}/favorite/{pid} → 204 | 401 | 403 | 404 | 500
    def favorite_product(self, ctx: AuthContext, rid: UUID, pid: UUID) -> NoContent:
        try:
            rep = self.provider.get_report(ctx, rid=rid)
            if pid not in rep.favorite_product_ids:
                rep = self._touch(
                    rep, favorite_product_ids=[*rep.favorite_product_ids, pid]
                )
                self.provider.put_report(ctx, report=rep)
            return NoContent()
        except Exception as e:
            self._handle_error(e, "Report or product not found.")

    # DELETE /report/{rid}/favorite/{pid} → 204 | 401 | 403 | 404 | 500
    def unfavorite_product(self, ctx: AuthContext, rid: UUID, pid: UUID) -> NoContent:
        try:
            rep = self.provider.get_report(ctx, rid=rid)
            new_ids = [i for i in rep.favorite_product_ids if i != pid]
            if len(new_ids) != len(rep.favorite_product_ids):
                rep = self._touch(rep, favorite_product_ids=new_ids)
                self.provider.put_report(ctx, report=rep)
            return NoContent()
        except Exception as e:
            self._handle_error(e, "Report or product not found.")
