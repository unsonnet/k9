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

from models.auth import AuthContext
from models.report import (
    CreateReportRequest,
    ListReportsOKBody,
    ListReportsParams,
    Report,
    ReportSummary,
    StoredReport,
    StoredReportSummary,
    UpdateReportRequest,
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
            _NoopProductResolver,
            _NoopReportDBProvider,
            _NoopUserResolver,
        )

        self.provider = _NoopReportDBProvider()
        self.products = _NoopProductResolver()
        self.users = _NoopUserResolver()

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
    def _touch(r: StoredReport, **updates) -> StoredReport:
        return r.model_copy(update={**updates, "updatedAt": datetime.now(timezone.utc)})

    def _public_summary(
        self, ctx: AuthContext, s: StoredReportSummary
    ) -> ReportSummary:
        ref = self.products.get_summary(ctx, pid=s.referenceId)
        return ReportSummary(
            id=s.id,
            author=s.author,
            title=s.title,
            date=s.createdAt,
            reference=ref,
        )

    def _public_report(self, ctx: AuthContext, r: StoredReport) -> Report:
        ref = self.products.get_product(ctx, pid=r.referenceId)
        favs = [self.products.get_product(ctx, pid=pid) for pid in r.favoriteIds]
        return Report(
            id=r.id,
            author=r.author,
            title=r.title,
            date=r.createdAt,
            reference=ref,
            favorites=favs,
        )

    # ─────────── Endpoints ───────────
    # GET /report → 200 | 401 | 403 | 500
    def list_reports(
        self, ctx: AuthContext, params: ListReportsParams
    ) -> OK[ListReportsOKBody]:
        try:
            res = self.provider.list_reports(
                ctx,
                limit=params.limit,
                next_token=params.nextToken,
                everyone=params.everyone,
            )
            body = ListReportsOKBody(
                total=res.total,
                reports=[self._public_summary(ctx, s) for s in res.reports],
                nextToken=res.nextToken,
            )
            return OK(body)
        except Exception as e:
            self._handle_error(e, "Failed to list reports.")

    # POST /report → 201 | 400 | 401 | 403 | 404 | 500
    def create_report(
        self, ctx: AuthContext, payload: CreateReportRequest
    ) -> Created[Report]:
        try:
            author_id = self.users.get_user_id(ctx)
            stored = self.provider.post_report(
                ctx,
                author=author_id,
                title=payload.title,
                reference=payload.reference,
            )
            return Created(self._public_report(ctx, stored))
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
            reference_id = payload.reference or rep.referenceId
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
            if pid not in rep.favoriteIds:
                rep = self._touch(rep, favoriteIds=[*rep.favoriteIds, pid])
                self.provider.put_report(ctx, report=rep)
            return NoContent()
        except Exception as e:
            self._handle_error(e, "Report or product not found.")

    # DELETE /report/{rid}/favorite/{pid} → 204 | 401 | 403 | 404 | 500
    def unfavorite_product(self, ctx: AuthContext, rid: UUID, pid: UUID) -> NoContent:
        try:
            rep = self.provider.get_report(ctx, rid=rid)
            new_ids = [i for i in rep.favoriteIds if i != pid]
            if len(new_ids) != len(rep.favoriteIds):
                rep = self._touch(rep, favoriteIds=new_ids)
                self.provider.put_report(ctx, report=rep)
            return NoContent()
        except Exception as e:
            self._handle_error(e, "Report or product not found.")
