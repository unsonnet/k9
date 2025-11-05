#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Sequence
from uuid import UUID

from pydantic import BaseModel
from pydantic.types import NonNegativeInt

from models.domain.auth import AuthContext
from models.shared.types import NonEmptyStr
from models.domain.product import Product, ProductSummary
from models.domain.report import ReportEntity, ReportSummary


# ──────────────────────────────────────────────────────────────────────────────
# Provider Interfaces
# ──────────────────────────────────────────────────────────────────────────────
class ListReportsResult(BaseModel):
    total: NonNegativeInt
    reports: Sequence[ReportSummary]
    nextToken: NonEmptyStr | None = None


class ReportDBProvider(ABC):
    """Backend contract for report persistence."""

    @abstractmethod
    def get_report(self, ctx: AuthContext, *, rid: UUID) -> ReportEntity: ...

    @abstractmethod
    def post_report(
        self,
        ctx: AuthContext,
        *,
        author: UUID,
        title: NonEmptyStr,
        reference: UUID,
    ) -> ReportEntity: ...

    @abstractmethod
    def put_report(self, ctx: AuthContext, *, report: ReportEntity) -> ReportEntity: ...

    @abstractmethod
    def delete_report(self, ctx: AuthContext, *, rid: UUID) -> None: ...

    @abstractmethod
    def list_reports(
        self,
        ctx: AuthContext,
        *,
        limit: int | None,
        next_token: str | None,
        everyone: bool | None,
    ) -> ListReportsResult: ...


class ProductResolver(ABC):
    """Dependency to resolve full Product or ProductSummary by id."""

    @abstractmethod
    def get_product(self, ctx: AuthContext, *, pid: UUID) -> Product: ...

    @abstractmethod
    def get_summary(self, ctx: AuthContext, *, pid: UUID) -> ProductSummary: ...


class UserResolver(ABC):
    """Dependency to resolve the current user from the auth context."""

    @abstractmethod
    def get_user_id(self, ctx: AuthContext) -> UUID: ...


# Default no-ops used by service constructors unless overridden
class NoopReportDBProvider(ReportDBProvider):  # pragma: no cover - placeholder
    def get_report(self, *_, **__) -> StoredReport:  # type: ignore[override]
        raise NotImplementedError("ReportDBProvider not configured")

    def post_report(self, *_, **__) -> StoredReport:  # type: ignore[override]
        raise NotImplementedError("ReportDBProvider not configured")

    def put_report(self, *_, **__) -> StoredReport:  # type: ignore[override]
        raise NotImplementedError("ReportDBProvider not configured")

    def delete_report(self, *_, **__) -> None:  # type: ignore[override]
        raise NotImplementedError("ReportDBProvider not configured")

    def list_reports(self, *_, **__) -> ListReportsResult:  # type: ignore[override]
        raise NotImplementedError("ReportDBProvider not configured")


class NoopProductResolver(ProductResolver):  # pragma: no cover - placeholder
    def get_product(self, *_, **__) -> Product:  # type: ignore[override]
        raise NotImplementedError("ProductResolver not configured")

    def get_summary(self, *_, **__) -> ProductSummary:  # type: ignore[override]
        raise NotImplementedError("ProductResolver not configured")


class NoopUserResolver(UserResolver):  # pragma: no cover - placeholder
    def get_user_id(self, *_, **__) -> UUID:  # type: ignore[override]
        raise NotImplementedError("UserResolver not configured")
