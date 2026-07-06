import base64
import json
from decimal import Decimal
from typing import Any, Iterable, Mapping, Protocol
from urllib.parse import urlparse

import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection
from shared.config import GrantSpec, is_set, missing, settings
from shared.errors import (
    DomainForbidden,
    DomainInvariantViolation,
    DomainNotFound,
    DomainRateLimited,
)
from shared.providers import BaseProvider, ExceptionMap, apimethod
from shared.providers.opensearch import Search
from types_boto3_dynamodb.service_resource import Table
from types_boto3_geo_places import LocationServicePlacesV2Client

from .models import GeoPoint, Location, Page

__all__ = [
    "LocationProvider",
    "AWSLocationProvider",
]


class LocationProvider(Protocol):
    @property
    def permissions(self) -> Iterable[GrantSpec]: ...

    def list_locations(
        self,
        *,
        id: str,
        geo: tuple[float, float, int] | missing,
        limit: int,
        cursor: str | missing,
    ) -> Page: ...

    def create_location(
        self,
        *,
        id: str,
        sid: str,
        street: str,
        city: str,
        state: str,
        zip: str,
    ) -> Location: ...

    def read_location(
        self,
        *,
        id: str,
        sid: str,
    ) -> Location: ...

    def update_location(
        self,
        *,
        id: str,
        sid: str,
        street: str | missing,
        city: str | missing,
        state: str | missing,
        zip: str | missing,
    ) -> Location: ...

    def delete_location(
        self,
        *,
        id: str,
        sid: str,
    ) -> None: ...


# ──── AWS Location Provider ───────────────────────────────────────────────────────────


class AWSLocationProvider(BaseProvider):
    _db: Table
    _os: OpenSearch
    _os_idx: str
    _loc: LocationServicePlacesV2Client

    def __init__(
        self,
        *,
        region: str | None = None,
        company_table: str | None = None,
        company_index: str | None = None,
        opensearch_endpoint: str | None = None,
    ) -> None:
        region = region or settings.aws_region
        # dynamodb
        table = company_table or settings.dynamodb_table
        self._db = boto3.resource("dynamodb", region).Table(table)
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
        gx = self._loc.exceptions
        return {
            DomainForbidden: [
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

    def _geocode(
        self, street: str, city: str, state: str, zip: str
    ) -> tuple[Decimal, Decimal]:
        response = self._loc.geocode(
            QueryText=f"{street}, {city}, {state} {zip}, USA",
            MaxResults=1,
        )
        match response:
            case {"ResultItems": [{"Position": [float(lon), float(lat)]}, *_]}:
                return Decimal(lat), Decimal(lon)
        raise DomainInvariantViolation(f"Unexpected geocode address: {response}")

    @classmethod
    def _location(cls, response: Mapping[str, Any]) -> Location:
        match response:
            case {
                "sk": str(xsid),
                "street": str(street),
                "city": str(city),
                "state": str(state),
                "zip": str(zip),
                "geo": {"lat": Decimal() as lat, "lon": Decimal() as lon},
            }:
                return Location(
                    id=xsid.removeprefix("LOCATION#"),
                    street=street,
                    city=city,
                    state=state,
                    zip=zip,
                    geo=GeoPoint(lat=lat, lon=lon),
                )
        raise DomainInvariantViolation(f"Unexpected dynamodb location: {response}")

    @classmethod
    def _page(cls, response: Mapping[str, Any]) -> Page:
        response = dict(response)
        response.setdefault("PaginationToken", None)
        match response:
            case {
                "Items": list(locations),
                "Cursor": list() | None as xcursor,
            }:
                return Page(
                    locations=[cls._location(raw) for raw in locations],
                    cursor=cls._encode_cursor(xcursor) if xcursor else None,
                )
        raise DomainInvariantViolation(f"Unexpected opensearch page: {response}")

    # ──── Public Methods ────

    @apimethod
    def list_locations(
        self,
        *,
        id: str,
        geo: tuple[float, float, int] | missing,
        limit: int,
        cursor: str | missing,
    ) -> Page:
        # TODO: implement filtering by company id
        xcursor = self._decode_cursor(cursor) if is_set(cursor) else None
        return self._page(
            Search(using=self._os, index=self._os_idx)
            .near("locations", coord=geo if is_set(geo) else None)
            .execute(limit=limit, cursor=xcursor)
        )

    @apimethod
    def create_location(
        self,
        *,
        id: str,
        sid: str,
        street: str,
        city: str,
        state: str,
        zip: str,
    ) -> Location:
        # TODO: make sure this is right
        lat, lon = self._geocode(street, city, state, zip)
        self._db.put_item(
            Item={
                "pk": f"COMPANY#{id}",
                "sk": f"LOCATION#{sid}",
                "street": street,
                "city": city,
                "state": state,
                "zip": zip,
                "geo": {"lat": lat, "lon": lon},
            },
            ConditionExpression="attribute_not_exists(pk) AND attribute_not_exists(sk)",
        )
        return self.read_location(id=id, sid=sid)

    @apimethod
    def read_location(
        self,
        *,
        id: str,
        sid: str,
    ) -> Location:
        # TODO: make sure this is right
        response = self._db.get_item(
            Key={"pk": f"COMPANY#{id}", "sk": f"LOCATION#{sid}"},
            ConsistentRead=True,
        )
        if "Item" not in response:
            raise DomainNotFound
        return self._location(response["Item"])

    @apimethod
    def update_location(
        self,
        *,
        id: str,
        sid: str,
        street: str | missing,
        city: str | missing,
        state: str | missing,
        zip: str | missing,
    ) -> Location:
        # TODO: make sure this is right
        updates: dict[str, Any] = {}
        if is_set(street):
            updates["street"] = street
        if is_set(city):
            updates["city"] = city
        if is_set(state):
            updates["state"] = state
        if is_set(zip):
            updates["zip"] = zip
        self._db.update_item(
            Key={"pk": f"COMPANY#{id}", "sk": f"LOCATION#{sid}"},
            UpdateExpression="SET " + ", ".join(f"#{k} = :{k}" for k in updates),
            ExpressionAttributeNames={f"#{k}": k for k in updates},
            ExpressionAttributeValues={f":{k}": v for k, v in updates.items()},
            ConditionExpression="attribute_exists(pk) AND attribute_exists(sk)",
        )
        return self.read_location(id=id, sid=sid)

    @apimethod
    def delete_location(
        self,
        *,
        id: str,
        sid: str,
    ) -> None:
        # TODO: make sure this is right
        self._db.delete_item(
            Key={"pk": f"COMPANY#{id}", "sk": f"LOCATION#{sid}"},
            ConditionExpression="attribute_exists(pk) AND attribute_exists(sk)",
        )
        return None
