import base64
import json
from decimal import Decimal
from typing import Any, Iterable, Mapping, Protocol

import boto3
from boto3.dynamodb.conditions import Key
from shared.config import GrantSpec, is_set, missing, settings
from shared.errors import (
    DomainForbidden,
    DomainInvariantViolation,
    DomainNotFound,
    DomainRateLimited,
)
from shared.providers import BaseProvider, ExceptionMap, apimethod
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
    _loc: LocationServicePlacesV2Client

    def __init__(
        self,
        *,
        region: str | None = None,
        company_table: str | None = None,
    ) -> None:
        region = region or settings.aws_region
        # dynamodb
        table = company_table or settings.dynamodb_table
        self._db = boto3.resource("dynamodb", region).Table(table)
        # location
        self._loc = boto3.client("geo-places", region_name=region)

    @property
    def permissions(self) -> Iterable[GrantSpec]:
        yield GrantSpec(
            actions=(
                "dynamodb:DeleteItem",
                "dynamodb:GetItem",
                "dynamodb:PutItem",
                "dynamodb:Query",
                "dynamodb:UpdateItem",
            ),
            resources=("dynamodb-table",),
        )
        yield GrantSpec(
            actions=("geo-places:Geocode",),
            resources=("*",),
        )

    @property
    def exception_map(self) -> ExceptionMap:
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
    def _encode_cursor(cursor: Mapping[str, Any]) -> str:
        payload = json.dumps(dict(cursor), separators=(",", ":"), ensure_ascii=False)
        payload = payload.encode("utf-8")
        return base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")

    @staticmethod
    def _decode_cursor(cursor: str) -> Mapping[str, Any]:
        try:
            padding = "=" * (-len(cursor) % 4)
            payload = base64.urlsafe_b64decode((cursor + padding).encode("ascii"))
            value = json.loads(payload.decode("utf-8"))
        except Exception as exc:
            raise ValueError("Invalid cursor") from exc
        if not isinstance(value, dict):
            raise ValueError("Invalid cursor")
        return value

    @staticmethod
    def _company_pk(id: str) -> str:
        return f"COMPANY#{id}"

    @staticmethod
    def _meta_sk() -> str:
        return "META"

    @staticmethod
    def _location_sk(id: str) -> str:
        return f"LOCATION#{id}"

    @staticmethod
    def _location_entity_type() -> str:
        return "LOCATION"

    @classmethod
    def _distance_km(
        cls,
        *,
        lat_a: float,
        lon_a: float,
        lat_b: float,
        lon_b: float,
    ) -> float:
        from math import asin, cos, radians, sin, sqrt

        earth_radius_km = 6371.0
        dlat = radians(lat_b - lat_a)
        dlon = radians(lon_b - lon_a)
        lat_a = radians(lat_a)
        lat_b = radians(lat_b)

        a = sin(dlat / 2.0) ** 2 + cos(lat_a) * cos(lat_b) * sin(dlon / 2.0) ** 2
        return 2.0 * earth_radius_km * asin(sqrt(a))

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
    def _page(
        cls,
        *,
        locations: list[Mapping[str, Any]],
        cursor: Mapping[str, Any] | None,
    ) -> Page:
        return Page(
            locations=[cls._location(raw) for raw in locations],
            cursor=cls._encode_cursor(cursor) if cursor else None,
        )

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
        xcursor = self._decode_cursor(cursor) if is_set(cursor) else None

        payload: dict[str, Any] = {
            "KeyConditionExpression": (
                Key("pk").eq(self._company_pk(id)) & Key("sk").begins_with("LOCATION#")
            ),
            "Limit": limit,
            "ConsistentRead": True,
        }
        if xcursor is not None:
            payload["ExclusiveStartKey"] = dict(xcursor)

        response = self._db.query(**payload)
        items: list[Mapping[str, Any]] = response.get("Items", [])

        if is_set(geo):
            lat, lon, radius_km = geo
            items = [
                item
                for item in items
                if self._distance_km(
                    lat_a=lat,
                    lon_a=lon,
                    lat_b=float(item["geo"]["lat"]),
                    lon_b=float(item["geo"]["lon"]),
                )
                <= radius_km
            ]

        return self._page(
            locations=items,
            cursor=response.get("LastEvaluatedKey"),
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
        company = self._db.get_item(
            Key={"pk": self._company_pk(id), "sk": self._meta_sk()},
            ConsistentRead=True,
        )
        if "Item" not in company:
            raise DomainNotFound

        lat, lon = self._geocode(street, city, state, zip)
        self._db.put_item(
            Item={
                "entity_type": self._location_entity_type(),
                "pk": self._company_pk(id),
                "sk": self._location_sk(sid),
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
        response = self._db.get_item(
            Key={"pk": self._company_pk(id), "sk": self._location_sk(sid)},
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
        current = self.read_location(id=id, sid=sid)

        next_street = street if is_set(street) else current.street
        next_city = city if is_set(city) else current.city
        next_state = state if is_set(state) else current.state
        next_zip = zip if is_set(zip) else current.zip

        updates: dict[str, Any] = {"entity_type": self._location_entity_type()}
        if is_set(street):
            updates["street"] = street
        if is_set(city):
            updates["city"] = city
        if is_set(state):
            updates["state"] = state
        if is_set(zip):
            updates["zip"] = zip

        if is_set(street) or is_set(city) or is_set(state) or is_set(zip):
            lat, lon = self._geocode(next_street, next_city, next_state, next_zip)
            updates["geo"] = {"lat": lat, "lon": lon}

        if not updates:
            return current

        self._db.update_item(
            Key={"pk": self._company_pk(id), "sk": self._location_sk(sid)},
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
        self._db.delete_item(
            Key={"pk": self._company_pk(id), "sk": self._location_sk(sid)},
            ConditionExpression="attribute_exists(pk) AND attribute_exists(sk)",
        )
        return None
