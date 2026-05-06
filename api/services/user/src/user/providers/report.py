from datetime import datetime
from typing import Protocol, Sequence

from shared.abc import DataModel

__all__ = [
    "Report",
    "ReportPage",
    "ReportProvider",
]

# ──── Report Models ───────────────────────────────────────────────────────────────────


class Report(DataModel, frozen=True):
    id: str
    user: str
    title: str
    final: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ReportPage(DataModel, frozen=True):
    reports: Sequence[Report]
    cursor: str | None = None


# ──── Report Protocol ─────────────────────────────────────────────────────────────────


class ReportProvider(Protocol):
    def list_reports(
        self,
        *,
        user: str,
        q: str | None = None,
        final: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        limit: int | None = None,
        cursor: str | None = None,
    ) -> ReportPage: ...
