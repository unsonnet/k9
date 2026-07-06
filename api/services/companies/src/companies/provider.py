import base64
import json
from typing import Any, Iterable, Mapping, Protocol
from urllib.parse import urlparse

import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection
from pydantic import HttpUrl
from shared.config import GrantSpec, is_set, missing, settings
from shared.errors import (
    DomainForbidden,
    DomainInvariantViolation,
    DomainNotFound,
    DomainRateLimited,
)
from shared.helpers import dt, now
from shared.providers import BaseProvider, ExceptionMap, apimethod
from shared.providers.opensearch import Search
from types_boto3_dynamodb.service_resource import Table
from types_boto3_s3.service_resource import Bucket

from .models import (
    Company,
    CompanySummary,
    Contact,
    Location,
    Page,
    Sector,
    UploadForm,
)

__all__ = [
    "CompanyProvider",
    "AWSCompanyProvider",
]


class CompanyProvider(Protocol):
    @property
    def permissions(self) -> Iterable[GrantSpec]: ...

    def list_companies(
        self,
        *,
        sector: list[Sector] | missing,
        name: str | missing,
        geo: tuple[float, float, int] | missing,
        limit: int,
        cursor: str | missing,
    ) -> Page: ...

    def create_company(
        self,
        *,
        id: str,
        sector: Sector,
        name: str,
        website: HttpUrl | None,
    ) -> Company: ...

    def read_company(
        self,
        *,
        id: str,
    ) -> Company: ...

    def update_company(
        self,
        *,
        id: str,
        sector: Sector | missing,
        name: str | missing,
        website: HttpUrl | None | missing,
    ) -> Company: ...

    def delete_company(
        self,
        *,
        id: str,
    ) -> None: ...

    def upload_logo(
        self,
        *,
        id: str,
        content_type: str,
        max_bytes: int,
        max_seconds: int,
    ) -> UploadForm: ...


# ──── AWS Company Provider ────────────────────────────────────────────────────────────


class AWSCompanyProvider(BaseProvider):
    _db: Table
    _s3: Bucket
    _s3_url: str
    _os: OpenSearch
    _os_idx: str

    def __init__(
        self,
        *,
        region: str | None = None,
        bucket: str | None = None,
        company_table: str | None = None,
        company_index: str | None = None,
        opensearch_endpoint: str | None = None,
    ) -> None:
        region = region or settings.aws_region
        # dynamodb
        table = company_table or settings.dynamodb_table
        self._db = boto3.resource("dynamodb", region).Table(table)
        # s3
        bucket = bucket or settings.s3_bucket
        self._s3 = boto3.resource("s3", region).Bucket(bucket)
        self._s3_url = f"https://{bucket}.s3.{region}.amazonaws.com"
        # opensearch
        endpoint = urlparse(opensearch_endpoint or settings.opensearch_endpoint)
        self._os = OpenSearch(
            hosts=[{"host": endpoint.hostname, "port": endpoint.port}],
            http_auth=settings.aws_auth(boto3.Session()),
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
            timeout=300,
        )
        self._os_idx = company_index or settings.opensearch_index_companies

    @property
    def permissions(self) -> Iterable[GrantSpec]:
        yield GrantSpec(
            actions=(
                "dynamodb:DeleteItem",
                "dynamodb:GetItem",
                "dynamodb:PutItem",
                "dynamodb:UpdateItem",
            ),
            resources=("dynamodb-table",),
        )
        yield GrantSpec(
            actions=(
                "s3:GetObject",
                "s3:PutObject",
            ),
            resources=("s3-bucket",),
        )
        yield GrantSpec(
            actions=("es:ESHttpPost",),
            resources=("opensearch-domain",),
        )

    @property
    def _exception_map(self) -> ExceptionMap:
        dbx = self._db.meta.client.exceptions
        s3x = self._s3.meta.client.exceptions
        return {
            DomainForbidden: [
                s3x.AccessDenied,
            ],
            DomainRateLimited: [
                dbx.ProvisionedThroughputExceededException,
                dbx.RequestLimitExceeded,
                dbx.ThrottlingException,
            ],
            DomainInvariantViolation: [
                dbx.ItemCollectionSizeLimitExceededException,
                dbx.ReplicatedWriteConflictException,
                dbx.TransactionConflictException,
            ],
            DomainNotFound: [
                dbx.ConditionalCheckFailedException,
                dbx.ResourceNotFoundException,
                s3x.NoSuchBucket,
                s3x.NoSuchKey,
            ],
        }

    # ──── Private Methods ────

    @staticmethod
    def _encode_cursor(sort: list[Any]) -> str:
        payload = json.dumps(sort, separators=(",", ":"), ensure_ascii=False)
        payload = payload.encode("utf-8")
        return base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")

    @staticmethod
    def _decode_cursor(cursor: str) -> list[Any]:
        try:
            padding = "=" * (-len(cursor) % 4)
            payload = base64.urlsafe_b64decode((cursor + padding).encode("ascii"))
            value = json.loads(payload.decode("utf-8"))
        except Exception as exc:
            raise ValueError("Invalid cursor") from exc
        if not isinstance(value, list):
            raise ValueError("Invalid cursor")
        return value

    @classmethod
    def _company(cls, response: Mapping[str, Any]) -> Company:
        response = dict(response)
        response.setdefault("updated_at", None)
        match response:
            case {
                "id": str(id),
                "sector": str(sector),
                "name": str(name),
                "logo": str(logo),
                "website": str(website),
                "locations": list() as locations,
                "contacts": list() as contacts,
                "created_at": str(created_at),
                "updated_at": str() | None as updated_at,
            }:
                return Company(
                    id=id,
                    sector=Sector(sector),
                    name=name,
                    logo=HttpUrl(logo),
                    website=HttpUrl(website),
                    locations=[Location.model_validate(i) for i in locations],
                    contacts=[Contact.model_validate(i) for i in contacts],
                    created_at=dt(created_at),
                    updated_at=dt(updated_at),
                )
        raise DomainInvariantViolation(f"Unexpected dynamodb company: {response}")

    @classmethod
    def _company_summary(cls, response: Mapping[str, Any]) -> CompanySummary:
        match response:
            case {
                "source": {
                    "id": str(id),
                    "sector": str(sector),
                    "name": str(name),
                    "logo": str(logo),
                    "website": str(website),
                    "locations": list() as locations,
                }
            }:
                return CompanySummary(
                    id=id,
                    sector=Sector(sector),
                    name=name,
                    logo=HttpUrl(logo),
                    website=HttpUrl(website),
                    locations=[Location.model_validate(i) for i in locations],
                )
        raise DomainInvariantViolation(
            f"Unexpected opensearch company summary: {response}"
        )

    @classmethod
    def _page(cls, response: Mapping[str, Any]) -> Page:
        response = dict(response)
        response.setdefault("PaginationToken", None)
        match response:
            case {
                "Items": list(companies),
                "Cursor": list() | None as xcursor,
            }:
                return Page(
                    companies=[cls._company_summary(raw) for raw in companies],
                    cursor=cls._encode_cursor(xcursor) if xcursor else None,
                )
        raise DomainInvariantViolation(f"Unexpected opensearch page: {response}")

    @classmethod
    def _upload_form(cls, response: Mapping[str, Any]) -> UploadForm:
        match response:
            case {
                "url": str(url),
                "fields": dict(fields),
            }:
                return UploadForm(
                    url=url,
                    fields=fields,
                )
        raise DomainInvariantViolation(f"Unexpected s3 upload form: {response}")

    # ──── Public Methods ────

    @apimethod
    def list_companies(
        self,
        *,
        sector: list[Sector] | missing,
        name: str | missing,
        geo: tuple[float, float, int] | missing,
        limit: int,
        cursor: str | missing,
    ) -> Page:
        xcursor = self._decode_cursor(cursor) if is_set(cursor) else None
        return self._page(
            Search(using=self._os, index=self._os_idx)
            .key("sector", options=[str(i) for i in sector] if is_set(sector) else None)
            .text("name", query=name if is_set(name) else None)
            .near("locations", coord=geo if is_set(geo) else None)
            .execute(limit=limit, cursor=xcursor)
        )

    @apimethod
    def create_company(
        self,
        *,
        id: str,
        sector: Sector,
        name: str,
        website: HttpUrl | None,
    ) -> Company:
        self._db.put_item(
            Item={
                "id": id,
                "sector": sector.value,
                "name": name,
                "logo": None,
                "website": str(website) if website is not None else None,
                "locations": [],
                "contacts": [],
                "created_at": now().isoformat(),
                "updated_at": None,
            },
            ConditionExpression="attribute_not_exists(id)",
        )
        return self.read_company(id=id)

    @apimethod
    def read_company(
        self,
        *,
        id: str,
    ) -> Company:
        response = self._db.get_item(
            Key={"id": id},
            ConsistentRead=True,
        )
        if "Item" not in response:
            raise DomainNotFound
        return self._company(response["Item"])

    @apimethod
    def update_company(
        self,
        *,
        id: str,
        sector: Sector | missing,
        name: str | missing,
        website: HttpUrl | None | missing,
    ) -> Company:
        # TODO: setup as a suggestion
        updates: dict[str, Any] = {"updated_at": now().isoformat()}
        if is_set(sector):
            updates["sector"] = sector.value
        if is_set(name):
            updates["name"] = name
        if is_set(website):
            updates["website"] = str(website) if website is not None else None
        self._db.update_item(
            Key={"id": id},
            UpdateExpression="SET " + ", ".join(f"#{k} = :{k}" for k in updates),
            ExpressionAttributeNames={f"#{k}": k for k in updates},
            ExpressionAttributeValues={f":{k}": v for k, v in updates.items()},
            ConditionExpression="attribute_exists(id)",
        )
        return self.read_company(id=id)

    @apimethod
    def delete_company(
        self,
        *,
        id: str,
    ) -> None:
        self._db.delete_item(
            Key={"id": id},
            ConditionExpression="attribute_exists(id)",
        )
        return None

    @apimethod
    def upload_logo(
        self,
        *,
        id: str,
        content_type: str,
        max_bytes: int,
        max_seconds: int,
    ) -> UploadForm:
        return self._upload_form(
            self._s3.meta.client.generate_presigned_post(
                Bucket=self._s3.name,
                Key=f"companies/{id}/logo.jxl",
                Fields={"Content-Type": content_type},
                Conditions=[
                    {"Content-Type": content_type},
                    ["content-length-range", 1, max_bytes],
                ],
                ExpiresIn=max_seconds,
            )
        )
