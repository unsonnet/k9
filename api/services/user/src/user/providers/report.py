import base64
import json
from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any, Protocol, Sequence, overload

import boto3
from opensearchpy import AWSV4SignerAuth, OpenSearch, RequestsHttpConnection
from opensearchpy.exceptions import (
    AuthenticationException,
    AuthorizationException,
    ConnectionError,
    ConnectionTimeout,
    NotFoundError,
)
from pydantic import StrictBool, ValidationError, field_validator
from shared.abc import BaseProvider, DataModel, ExceptionMap, private_api
from shared.config import settings
from shared.errors import (
    DomainForbidden,
    DomainInvariantViolation,
    DomainNotFound,
    DomainRateLimited,
    assert_unreachable,
)

__all__ = [
    "Report",
    "ReportPage",
    "ReportProvider",
    "OpenSearchReportProvider",
]

# ──── Report Models ───────────────────────────────────────────────────────────────────


class Report(DataModel, frozen=True):
    id: str
    user: str
    title: str
    final: StrictBool
    created_at: datetime
    updated_at: datetime | None = None

    @field_validator("created_at", "updated_at", mode="after")
    @classmethod
    def verify_datetime(cls, value: datetime | None) -> datetime | None:
        match value:
            case datetime() as dt:
                return dt.astimezone(timezone.utc)
            case None:
                return None
            case _ as never:
                assert_unreachable(never)


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
        final: bool | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        limit: int | None = None,
        cursor: str | None = None,
    ) -> ReportPage: ...


# ──── AWS Report Provider ─────────────────────────────────────────────────────────────


class OpenSearchReportProvider(BaseProvider):
    _client: OpenSearch
    _index: str

    def __init__(
        self,
        *,
        region: str | None = None,
        endpoint: str | None = None,
        index: str | None = None,
        service: str = "aoss",
    ) -> None:
        region = region or settings.aws_region
        endpoint = endpoint or settings.opensearch_endpoint
        self._index = index or settings.opensearch_reports_index

        credentials = boto3.Session().get_credentials()
        if credentials is None:
            raise DomainInvariantViolation("Missing AWS credentials")

        self._client = OpenSearch(
            hosts=[
                {
                    "host": endpoint.removeprefix("https://").rstrip("/"),
                    "port": 443,
                }
            ],
            http_auth=AWSV4SignerAuth(credentials, region, service),
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
        )

    @property
    def _exception_map(self) -> ExceptionMap:
        return {
            DomainForbidden: [
                AuthenticationException,
                AuthorizationException,
            ],
            DomainRateLimited: [
                ConnectionTimeout,
                ConnectionError,
            ],
            DomainNotFound: [
                NotFoundError,
            ],
        }

    # ──── Helper Methods ────

    @overload
    def _dt(self, value: datetime) -> str: ...
    @overload
    def _dt(self, value: None) -> None: ...
    def _dt(self, value: datetime | None) -> str | None:
        match value:
            case datetime() as dt:
                return dt.astimezone(timezone.utc).isoformat()
            case None:
                return None
            case _ as never:
                assert_unreachable(never)

    def _cursor(self, value: Sequence[Any] | None) -> str | None:
        match value:
            case [*_]:
                raw = json.dumps(value, separators=(",", ":")).encode("utf-8")
                return base64.urlsafe_b64encode(raw).decode("utf-8")
            case None:
                return None
            case _ as never:
                assert_unreachable(never)

    def _search_after(self, cursor: str | None) -> list[Any] | None:
        if cursor is None:
            return None

        try:
            raw = base64.urlsafe_b64decode(cursor.encode("utf-8"))
            value = json.loads(raw.decode("utf-8"))
        except Exception as exc:
            raise DomainInvariantViolation("Invalid report cursor") from exc

        match value:
            case [*values] if all(
                item is None or isinstance(item, (str, int, float, bool))
                for item in values
            ):
                return values
        raise DomainInvariantViolation("Invalid report cursor")

    def _report(self, response: Mapping[str, Any]) -> Report:
        match response:
            case {"_source": Mapping() as source}:
                try:
                    return Report.model_validate(source)
                except ValidationError as exc:
                    raise DomainInvariantViolation(
                        f"Unexpected opensearch response: {response}"
                    ) from exc
        raise DomainInvariantViolation(f"Unexpected opensearch response: {response}")

    def _query(
        self,
        *,
        user: str,
        q: str | None,
        final: bool | None,
        date_from: datetime | None,
        date_to: datetime | None,
        limit: int | None,
        cursor: str | None,
    ) -> dict[str, Any]:
        filters: list[dict[str, Any]] = [
            {"term": {"user": user}},
        ]

        if final is not None:
            filters.append({"term": {"final": final}})

        if date_from or date_to:
            filters.append(
                {
                    "range": {
                        "created_at": {
                            **(
                                {"gte": value} if (value := self._dt(date_from)) else {}
                            ),
                            **({"lte": value} if (value := self._dt(date_to)) else {}),
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
                {"search_after": search_after}
                if (search_after := self._search_after(cursor))
                else {}
            ),
        }

    def _page(self, response: Mapping[str, Any]) -> ReportPage:
        match response:
            case {"hits": {"hits": list(hits)}}:
                return ReportPage(
                    reports=[self._report(hit) for hit in hits],
                    cursor=self._cursor(hits[-1].get("sort")) if hits else None,
                )
        raise DomainInvariantViolation(f"Unexpected opensearch response: {response}")

    # ──── Private APIs ────

    @private_api
    def list_reports(
        self,
        *,
        user: str,
        q: str | None = None,
        final: bool | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        limit: int | None = None,
        cursor: str | None = None,
    ) -> ReportPage:
        return self._page(
            self._client.search(
                index=self._index,
                body=self._query(
                    user=user,
                    q=q,
                    final=final,
                    date_from=date_from,
                    date_to=date_to,
                    limit=limit,
                    cursor=cursor,
                ),
            )
        )
