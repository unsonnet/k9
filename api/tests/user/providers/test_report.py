import base64
import json
from datetime import datetime, timezone
from typing import Any, Mapping

import pytest
import user.providers.report as provider_module
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
from shared.providers.cognito import encode_id
from user.providers.report import Report, ReportPage

pytestmark = pytest.mark.unit


# ──── Helpers ─────────────────────────────────────────────────────────────────────────

INDEX = "reports"
USER_ID = "11111111-1111-1111-1111-111111111111"
REPORT_ID = "report-1"
REPORT_2_ID = "report-2"
CREATED_AT = datetime(2026, 1, 1, tzinfo=timezone.utc)
UPDATED_AT = datetime(2026, 1, 2, tzinfo=timezone.utc)

PROVIDER_ERROR_CASES = [
    pytest.param(
        AuthenticationException(401, "auth"),
        DomainForbidden,
        id="authentication",
    ),
    pytest.param(
        AuthorizationException(403, "forbidden"),
        DomainForbidden,
        id="authorization",
    ),
    pytest.param(
        ConnectionTimeout("timed-out"),
        DomainRateLimited,
        id="timeout",
    ),
    pytest.param(
        ConnectionError("connection-error"),
        DomainRateLimited,
        id="connection",
    ),
    pytest.param(
        NotFoundError(404, "missing"),
        DomainNotFound,
        id="not-found",
    ),
]


def make_cursor(values: list[Any]) -> str:
    raw = json.dumps(values, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("utf-8")


def report_source(
    *,
    id: str = REPORT_ID,
    user: str = USER_ID,
    title: str = "Quarterly report",
    final: bool = True,
    created_at: datetime = CREATED_AT,
    updated_at: datetime | None = UPDATED_AT,
) -> dict[str, Any]:
    return {
        "id": id,
        "xuser": encode_id(user),
        "title": title,
        "final": final,
        "created_at": created_at,
        "updated_at": updated_at,
    }


def report_hit(
    *,
    source: dict[str, Any],
    sort: list[Any] | None,
) -> dict[str, Any]:
    return {
        "_source": source,
        "sort": sort,
    }


def expected_report(
    *,
    id: str = REPORT_ID,
    user: str = USER_ID,
    title: str = "Quarterly report",
    final: bool = True,
    created_at: datetime = CREATED_AT,
    updated_at: datetime | None = UPDATED_AT,
) -> Report:
    return Report(
        id=id,
        user=user,
        title=title,
        final=final,
        created_at=created_at,
        updated_at=updated_at,
    )


class FakeSearchClient:
    def __init__(self, response: Mapping[str, Any]) -> None:
        self._response = response
        self.calls: list[dict[str, Any]] = []

    def search(self, **kwargs: Any) -> Mapping[str, Any]:
        self.calls.append(kwargs)
        return self._response


class RaisingSearchClient:
    def __init__(self, error: Exception) -> None:
        self._error = error

    def search(self, **_: Any) -> Mapping[str, Any]:
        raise self._error


def make_provider(client: Any) -> provider_module.OpenSearchReportProvider:
    provider = object.__new__(provider_module.OpenSearchReportProvider)
    provider._client = client
    provider._index = INDEX
    return provider


# ──── list_reports() ──────────────────────────────────────────────────────────────────


class TestListReports:
    def test_returns_page(self) -> None:
        client = FakeSearchClient(
            {
                "hits": {
                    "hits": [
                        report_hit(
                            source=report_source(),
                            sort=[1704067200, REPORT_ID],
                        ),
                        report_hit(
                            source=report_source(
                                id=REPORT_2_ID,
                                title="Incident summary",
                            ),
                            sort=[1704067100, REPORT_2_ID],
                        ),
                    ]
                }
            }
        )
        provider = make_provider(client)

        result = provider.list_reports(user=USER_ID, limit=10)

        assert client.calls == [
            {
                "index": INDEX,
                "body": {
                    "size": 10,
                    "query": {
                        "bool": {
                            "filter": [{"term": {"xuser": encode_id(USER_ID)}}],
                        }
                    },
                    "sort": [{"created_at": "desc"}, {"id": "asc"}],
                },
            }
        ]
        assert result == ReportPage(
            reports=[
                expected_report(),
                expected_report(
                    id=REPORT_2_ID,
                    title="Incident summary",
                ),
            ],
            cursor=make_cursor([1704067100, REPORT_2_ID]),
        )

    def test_passes_query_payload(self) -> None:
        client = FakeSearchClient({"hits": {"hits": []}})
        provider = make_provider(client)

        result = provider.list_reports(user=USER_ID, q="incident")

        assert result == ReportPage(reports=[], cursor=None)
        assert client.calls == [
            {
                "index": INDEX,
                "body": {
                    "size": 25,
                    "query": {
                        "bool": {
                            "filter": [{"term": {"xuser": encode_id(USER_ID)}}],
                            "must": [
                                {
                                    "bool": {
                                        "should": [
                                            {
                                                "term": {
                                                    "id": {
                                                        "value": "incident",
                                                        "boost": 10,
                                                        "case_insensitive": True,
                                                    }
                                                }
                                            },
                                            {
                                                "prefix": {
                                                    "id": {
                                                        "value": "incident",
                                                        "boost": 6,
                                                        "case_insensitive": True,
                                                    }
                                                }
                                            },
                                            {
                                                "match": {
                                                    "title": {
                                                        "query": "incident",
                                                        "operator": "and",
                                                        "boost": 4,
                                                    }
                                                }
                                            },
                                            {
                                                "match_phrase_prefix": {
                                                    "title": {
                                                        "query": "incident",
                                                        "boost": 2,
                                                    }
                                                }
                                            },
                                        ],
                                        "minimum_should_match": 1,
                                    }
                                }
                            ],
                        }
                    },
                    "sort": [
                        {"_score": "desc"},
                        {"created_at": "desc"},
                        {"id": "asc"},
                    ],
                },
            }
        ]

    def test_passes_bounded_limit(self) -> None:
        client = FakeSearchClient({"hits": {"hits": []}})
        provider = make_provider(client)

        provider.list_reports(user=USER_ID, limit=1000)

        assert client.calls[0]["body"]["size"] == 100

    def test_passes_cursor_when_provided(self) -> None:
        client = FakeSearchClient({"hits": {"hits": []}})
        provider = make_provider(client)

        provider.list_reports(user=USER_ID, cursor=make_cursor([1704067200, REPORT_ID]))

        assert client.calls[0]["body"]["search_after"] == [1704067200, REPORT_ID]

    def test_passes_date_filter(self) -> None:
        client = FakeSearchClient({"hits": {"hits": []}})
        provider = make_provider(client)

        provider.list_reports(
            user=USER_ID,
            date_from=datetime(2026, 1, 1, 1, tzinfo=timezone.utc),
            date_to=datetime(2026, 1, 2, 2, tzinfo=timezone.utc),
        )

        assert client.calls[0]["body"]["query"]["bool"]["filter"] == [
            {"term": {"xuser": encode_id(USER_ID)}},
            {
                "range": {
                    "created_at": {
                        "gte": "2026-01-01T01:00:00+00:00",
                        "lte": "2026-01-02T02:00:00+00:00",
                    }
                }
            },
        ]

    def test_rejects_invalid_cursor(self) -> None:
        client = FakeSearchClient({"hits": {"hits": []}})
        provider = make_provider(client)

        with pytest.raises(DomainInvariantViolation, match="Invalid report cursor"):
            provider.list_reports(user=USER_ID, cursor="not-a-valid-cursor")

        assert client.calls == []

    def test_rejects_unexpected_provider_response_shape(self) -> None:
        client = FakeSearchClient(
            {
                "hits": {
                    "hits": [
                        {
                            "_source": {
                                "id": REPORT_ID,
                            }
                        }
                    ]
                }
            }
        )
        provider = make_provider(client)

        with pytest.raises(
            DomainInvariantViolation, match="Unexpected opensearch response"
        ):
            provider.list_reports(user=USER_ID)

    @pytest.mark.parametrize(
        ("provider_error", "expected_error"),
        PROVIDER_ERROR_CASES,
    )
    def test_maps_provider_errors(
        self,
        provider_error: Exception,
        expected_error: type[Exception],
    ) -> None:
        provider = make_provider(RaisingSearchClient(provider_error))

        with pytest.raises(expected_error):
            provider.list_reports(user=USER_ID)
