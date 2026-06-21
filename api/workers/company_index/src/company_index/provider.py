from collections.abc import Iterable
from typing import Protocol
from urllib.parse import urlparse

import boto3
import opensearchpy.exceptions as osx
from opensearchpy import OpenSearch, RequestsHttpConnection
from pydantic import HttpUrl
from shared.config import GrantSpec, settings
from shared.errors import DomainInvariantViolation, DomainNotFound
from shared.provider import BaseProvider, ExceptionMap, apimethod

from .models import Address, CompanySector

__all__ = [
    "IndexProvider",
    "OpenSearchIndexProvider",
]


class IndexProvider(Protocol):
    @property
    def permissions(self) -> Iterable[GrantSpec]: ...

    def index_company(
        self,
        *,
        id: str,
        sector: CompanySector,
        name: str,
        logo: HttpUrl,
        website: HttpUrl,
        locations: list[Address],
    ) -> None: ...

    def unindex_company(
        self,
        *,
        id: str,
    ) -> None: ...


# ──── OpenSearch Index Provider ───────────────────────────────────────────────────────


class OpenSearchIndexProvider(BaseProvider):
    _os: OpenSearch
    _os_idx: str

    def __init__(
        self,
        *,
        region: str | None = None,
        company_index: str | None = None,
        opensearch_endpoint: str | None = None,
    ) -> None:
        region = region or settings.aws_region
        endpoint = urlparse(opensearch_endpoint or settings.opensearch_endpoint)
        self._os = OpenSearch(
            hosts=[{"host": endpoint.hostname, "port": endpoint.port}],
            http_auth=settings.aws_auth(boto3.Session(region_name=region)),
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
            timeout=300,
        )
        self._os_idx = company_index or f"{settings.opensearch_index}-companies"

    @property
    def _exception_map(self) -> ExceptionMap:
        return {
            DomainNotFound: [osx.NotFoundError],
            DomainInvariantViolation: [osx.ValidationException],
        }

    @property
    def permissions(self) -> Iterable[GrantSpec]:
        yield GrantSpec(
            actions=(
                "es:ESHttpPost",
                "es:ESHttpPut",
                "es:ESHttpDelete",
            ),
            resources=("opensearch-domain",),
        )

    # ──── Public Methods ────

    @apimethod
    def index_company(
        self,
        *,
        id: str,
        sector: CompanySector,
        name: str,
        logo: HttpUrl,
        website: HttpUrl,
        locations: list[Address],
    ) -> None:
        self._os.index(
            index=self._os_idx,
            id=id,
            body={
                "id": id,
                "sector": sector.value,
                "name": name,
                "logo": str(logo),
                "website": str(website),
                "locations": [location.model_dump() for location in locations],
            },
            params={"refresh": "wait_for"},
        )
        return None

    @apimethod
    def unindex_company(
        self,
        *,
        id: str,
    ) -> None:
        self._os.delete(
            index=self._os_idx,
            id=id,
            params={"refresh": "wait_for"},
        )
        return None
