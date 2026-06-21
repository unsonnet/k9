import base64
import json
from decimal import Decimal
from typing import Any, Iterable, Mapping, Protocol
from urllib.parse import urlparse

import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection
from pydantic import HttpUrl
from shared.config import GrantSpec, settings
from shared.errors import (
    DomainForbidden,
    DomainInvariantViolation,
    DomainNotFound,
    DomainRateLimited,
)
from shared.helpers import dt, now
from shared.provider import BaseProvider, ExceptionMap, apimethod
from shared.provider.opensearch import Search
from types_boto3_dynamodb.service_resource import Table
from types_boto3_geo_places import LocationServicePlacesV2Client
from types_boto3_s3.service_resource import Bucket

from .models import (
    Address,
    Company,
    CompanySector,
    CompanySummary,
    Contact,
    GeoPoint,
    Page,
    UploadForm,
)

__all__ = [
    "CompanyProvider",
    "DynamoDBCompanyProvider",
]


class CompanyProvider(Protocol):
    @property
    def permissions(self) -> Iterable[GrantSpec]: ...

    def list_companies(
        self,
        *,
        q: str | None,
        k: list[CompanySector] | None,
        g: tuple[float, float, int] | None,
        limit: int,
        cursor: str | None,
    ) -> Page: ...

    def create_company(
        self,
        *,
        id: str,
        sector: CompanySector,
        name: str,
        website: HttpUrl,
        locations: list[Address],
        contacts: list[Contact],
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
        sector: CompanySector | None,
        name: str | None,
        website: HttpUrl | None,
        locations: list[Address] | None,
        contacts: list[Contact] | None,
    ) -> Company: ...

    def delete_company(
        self,
        *,
        id: str,
    ) -> None: ...

    def generate_upload_form(
        self,
        *,
        id: str,
        content_type: str,
        max_bytes: int,
        max_seconds: int,
    ) -> UploadForm: ...


# ──── AWS Company Provider ────────────────────────────────────────────────────────────


class DynamoDBCompanyProvider(BaseProvider):
    _db: Table
    _s3: Bucket
    _s3_url: str
    _os: OpenSearch
    _os_idx: str
    _loc: LocationServicePlacesV2Client

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
        table = company_table or settings.dynamodb_table + "-companies"
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
        self._os_idx = company_index or settings.opensearch_index + "-companies"
        # location
        self._loc = boto3.client("geo-places", region_name=region)

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
        yield GrantSpec(
            actions=("geo-places:Geocode",),
            resources=("*",),
        )

    @property
    def _exception_map(self) -> ExceptionMap:
        dbx = self._db.meta.client.exceptions
        s3x = self._s3.meta.client.exceptions
        gx = self._loc.exceptions
        return {
            DomainForbidden: [
                s3x.AccessDenied,
                gx.AccessDeniedException,
            ],
            DomainRateLimited: [
                dbx.ProvisionedThroughputExceededException,
                dbx.RequestLimitExceeded,
                dbx.ThrottlingException,
                gx.ThrottlingException,
            ],
            DomainInvariantViolation: [
                dbx.ItemCollectionSizeLimitExceededException,
                dbx.ReplicatedWriteConflictException,
                dbx.TransactionConflictException,
                gx.ValidationException,
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

    def _geocode(self, loc: Address) -> Address:
        if loc.geo is not None:
            return loc
        response = self._loc.geocode(
            QueryText=f"{loc.street}, {loc.city}, {loc.state} {loc.zip}, USA",
            MaxResults=1,
        )
        match response:
            case {"ResultItems": [{"Position": [float(lon), float(lat)]}, *_]}:
                return loc.model_copy(
                    update={"geo": GeoPoint(lat=Decimal(lat), lon=Decimal(lon))}
                )
        raise DomainInvariantViolation(f"Unexpected geocode address: {response}")

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
                    sector=CompanySector(sector),
                    name=name,
                    logo=HttpUrl(logo),
                    website=HttpUrl(website),
                    locations=[Address.model_validate(i) for i in locations],
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
                    sector=CompanySector(sector),
                    name=name,
                    logo=HttpUrl(logo),
                    website=HttpUrl(website),
                    locations=[Address.model_validate(i) for i in locations],
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
        q: str | None,
        k: list[CompanySector] | None,
        g: tuple[float, float, int] | None,
        limit: int,
        cursor: str | None,
    ) -> Page:
        xcursor = self._decode_cursor(cursor) if cursor else None
        return self._page(
            Search(using=self._os, index=self._os_idx)
            .key("sector", options=[i.value for i in k] if k else None)
            .text("name", query=q)
            .near("locations", coord=g)
            .execute(limit=limit, cursor=xcursor)
        )

    @apimethod
    def create_company(
        self,
        *,
        id: str,
        sector: CompanySector,
        name: str,
        website: HttpUrl,
        locations: list[Address],
        contacts: list[Contact],
    ) -> Company:
        self._db.put_item(
            Item={
                "id": id,
                "sector": sector.value,
                "name": name,
                "logo": f"{self._s3_url}/companies/{id}/logo.jxl",
                "website": str(website),
                "locations": [self._geocode(i).model_dump() for i in locations],
                "contacts": [i.model_dump() for i in contacts],
                "created_at": now().isoformat(),
                "updated_at": None,
            },
            ConditionExpression="attribute_not_exists(id)",
        )
        self._s3.copy(
            Key=f"companies/{id}/logo.jxl",
            CopySource={
                "Bucket": self._s3.name,
                "Key": "companies/default/logo.jxl",
            },
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
        sector: CompanySector | None,
        name: str | None,
        website: HttpUrl | None,
        locations: list[Address] | None,
        contacts: list[Contact] | None,
    ) -> Company:
        updates: dict[str, Any] = {"updated_at": now().isoformat()}
        if sector is not None:
            updates["sector"] = sector.value
        if name is not None:
            updates["name"] = name
        if website is not None:
            updates["website"] = str(website)
        if locations is not None:
            updates["locations"] = [self._geocode(i).model_dump() for i in locations]
        if contacts is not None:
            updates["contacts"] = [i.model_dump() for i in contacts]
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
    def generate_upload_form(
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
