import base64
import json
from datetime import datetime, timezone
from typing import Any, Mapping

import pytest
import user.providers.report as report
from opensearchpy.exceptions import (
    AuthenticationException,
    AuthorizationException,
    ConnectionError,
    ConnectionTimeout,
    NotFoundError,
)
from shared.errors import (
    DomainForbidden,
    DomainInvariantViolation,
    DomainNotFound,
    DomainRateLimited,
)
from user.providers.report import Report, ReportPage

pytestmark = pytest.mark.unit


# ──── Helpers ─────────────────────────────────────────────────────────────────────────


INDEX = "reports"


def report_source(
    *,
    id: str = "report-1",
    user: str = "user-1",
    title: str = "Report One",
    final: bool = True,
    created_at: str = "2026-01-01T00:00:00+00:00",
    updated_at: str | None = "2026-01-02T00:00:00+00:00",
) -> dict[str, Any]:
    return {
        "id": id,
        "user": user,
        "title": title,
        "final": final,
        "created_at": created_at,
        **({"updated_at": updated_at} if updated_at is not None else {}),
    }


def report_hit(
    *,
    source: Mapping[str, Any] | None = None,
    sort: list[Any] | None = None,
) -> dict[str, Any]:
    return {
        "_source": dict(source or report_source()),
        **({"sort": sort} if sort is not None else {}),
    }


def report_cursor(value: list[Any]) -> str:
    raw = json.dumps(value, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("utf-8")


def list_reports_body(
    *,
    user: str = "user-1",
    q: str | None = None,
    final: bool | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    limit: int | None = None,
    cursor: str | None = None,
) -> dict[str, Any]:
    filters: list[dict[str, Any]] = [{"term": {"user": user}}]

    if final is not None:
        filters.append({"term": {"final": final}})

    if date_from or date_to:
        filters.append(
            {
                "range": {
                    "created_at": {
                        **(
                            {"gte": date_from.astimezone(timezone.utc).isoformat()}
                            if date_from
                            else {}
                        ),
                        **(
                            {"lte": date_to.astimezone(timezone.utc).isoformat()}
                            if date_to
                            else {}
                        ),
                    }
                }
            }
        )

    return {
        "size": min(limit or 25, 100),
        "query": {
            "bool": {
                "filter": filters,
                **(
                    {
                        "must": [
                            {
                                "match": {
                                    "title": {
                                        "query": q,
                                        "operator": "and",
                                    }
                                }
                            }
                        ]
                    }
                    if q
                    else {}
                ),
            }
        },
        "sort": [
            {"created_at": "desc"},
            {"id": "asc"},
        ],
        **(
            {"search_after": json.loads(base64.urlsafe_b64decode(cursor).decode())}
            if cursor
            else {}
        ),
    }


def make_provider(client: Any) -> report.OpenSearchReportProvider:
    provider = report.OpenSearchReportProvider.__new__(report.OpenSearchReportProvider)
    provider._client = client
    provider._index = INDEX
    return provider


class FakeOpenSearch:
    def __init__(self, response: Mapping[str, Any]) -> None:
        self.response = response
        self.calls: list[dict[str, Any]] = []

    def search(self, **kwargs: Any) -> Mapping[str, Any]:
        self.calls.append(kwargs)
        return self.response


class RaisingOpenSearch:
    def __init__(self, error: Exception) -> None:
        self.error = error

    def search(self, **_: Any) -> Mapping[str, Any]:
        raise self.error


# ──── Tests ───────────────────────────────────────────────────────────────────────────


# ──── list_reports() ──────────────────────────────────────────────────────────────────


class TestListReports:
    def test_uses_expected_payload_and_returns_report_page(self) -> None:
        cursor = report_cursor(["2025-12-31T00:00:00+00:00", "report-0"])
        client = FakeOpenSearch(
            {
                "hits": {
                    "hits": [
                        report_hit(
                            source=report_source(
                                id="report-1",
                                title="Report One",
                                final=True,
                            ),
                            sort=["2026-01-02T00:00:00+00:00", "report-2"],
                        ),
                        report_hit(
                            source=report_source(
                                id="report-2",
                                title="Report Two",
                                final=False,
                                created_at="2026-01-03T00:00:00+00:00",
                                updated_at=None,
                            ),
                            sort=["2026-01-01T00:00:00+00:00", "report-1"],
                        ),
                    ]
                }
            }
        )
        provider = make_provider(client)

        result = provider.list_reports(
            user="user-1",
            q="report",
            final=True,
            date_from=datetime(2026, 1, 1, tzinfo=timezone.utc),
            date_to=datetime(2026, 1, 31, 23, 59, 59, tzinfo=timezone.utc),
            limit=10,
            cursor=cursor,
        )

        assert client.calls == [
            {
                "index": INDEX,
                "body": list_reports_body(
                    user="user-1",
                    q="report",
                    final=True,
                    date_from=datetime(2026, 1, 1, tzinfo=timezone.utc),
                    date_to=datetime(2026, 1, 31, 23, 59, 59, tzinfo=timezone.utc),
                    limit=10,
                    cursor=cursor,
                ),
            }
        ]
        assert result == ReportPage(
            reports=[
                Report(
                    id="report-1",
                    user="user-1",
                    title="Report One",
                    final=True,
                    created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
                    updated_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
                ),
                Report(
                    id="report-2",
                    user="user-1",
                    title="Report Two",
                    final=False,
                    created_at=datetime(2026, 1, 3, tzinfo=timezone.utc),
                    updated_at=None,
                ),
            ],
            cursor=report_cursor(["2026-01-01T00:00:00+00:00", "report-1"]),
        )

    def test_uses_default_limit_when_limit_is_omitted(self) -> None:
        client = FakeOpenSearch({"hits": {"hits": []}})
        provider = make_provider(client)

        result = provider.list_reports(user="user-1")

        assert client.calls == [
            {
                "index": INDEX,
                "body": list_reports_body(),
            }
        ]
        assert result == ReportPage(reports=[], cursor=None)

    def test_clamps_limit_to_100(self) -> None:
        client = FakeOpenSearch({"hits": {"hits": []}})
        provider = make_provider(client)

        result = provider.list_reports(user="user-1", limit=200)

        assert client.calls == [
            {
                "index": INDEX,
                "body": list_reports_body(limit=200),
            }
        ]
        assert result == ReportPage(reports=[], cursor=None)

    def test_returns_empty_page_when_provider_returns_no_reports(self) -> None:
        client = FakeOpenSearch({"hits": {"hits": []}})
        provider = make_provider(client)

        result = provider.list_reports(user="user-1", limit=10)

        assert result == ReportPage(reports=[], cursor=None)

    def test_returns_cursor_from_last_hit_sort(self) -> None:
        client = FakeOpenSearch(
            {
                "hits": {
                    "hits": [
                        report_hit(sort=["2026-01-02T00:00:00+00:00", "report-2"]),
                        report_hit(sort=["2026-01-01T00:00:00+00:00", "report-1"]),
                    ]
                }
            }
        )
        provider = make_provider(client)

        result = provider.list_reports(user="user-1")

        assert result.cursor == report_cursor(["2026-01-01T00:00:00+00:00", "report-1"])

    @pytest.mark.parametrize(
        "invalid_cursor",
        [
            pytest.param("not-base64", id="not-base64"),
            pytest.param(report_cursor([{"unexpected": "shape"}]), id="non-sort-list"),
            pytest.param(
                base64.urlsafe_b64encode(
                    json.dumps({"bad": "shape"}).encode("utf-8")
                ).decode("utf-8"),
                id="not-list",
            ),
        ],
    )
    def test_rejects_invalid_cursor(self, invalid_cursor: str) -> None:
        client = FakeOpenSearch({"hits": {"hits": []}})
        provider = make_provider(client)

        with pytest.raises(DomainInvariantViolation):
            provider.list_reports(user="user-1", cursor=invalid_cursor)

        assert client.calls == []

    def test_rejects_unexpected_provider_response_shape(self) -> None:
        client = FakeOpenSearch({"unexpected": "shape"})
        provider = make_provider(client)

        with pytest.raises(DomainInvariantViolation):
            provider.list_reports(user="user-1")

    def test_rejects_unexpected_report_hit_shape(self) -> None:
        client = FakeOpenSearch({"hits": {"hits": [{"unexpected": "shape"}]}})
        provider = make_provider(client)

        with pytest.raises(DomainInvariantViolation):
            provider.list_reports(user="user-1")

    def test_rejects_invalid_report_payload(self) -> None:
        source = report_source()
        source["final"] = "true"

        client = FakeOpenSearch({"hits": {"hits": [report_hit(source=source)]}})
        provider = make_provider(client)

        with pytest.raises(DomainInvariantViolation):
            provider.list_reports(user="user-1")

    @pytest.mark.parametrize(
        ("provider_error", "expected_error"),
        [
            pytest.param(
                AuthenticationException(401, "unauthenticated"),
                DomainForbidden,
                id="authentication",
            ),
            pytest.param(
                AuthorizationException(403, "unauthorized"),
                DomainForbidden,
                id="authorization",
            ),
            pytest.param(
                ConnectionTimeout("timed out"),
                DomainRateLimited,
                id="timeout",
            ),
            pytest.param(
                ConnectionError("connection failed"),
                DomainRateLimited,
                id="connection",
            ),
            pytest.param(
                NotFoundError(404, "missing"),
                DomainNotFound,
                id="not-found",
            ),
        ],
    )
    def test_maps_provider_errors(
        self,
        provider_error: Exception,
        expected_error: type[Exception],
    ) -> None:
        provider = make_provider(RaisingOpenSearch(provider_error))

        with pytest.raises(expected_error):
            provider.list_reports(user="user-1")
