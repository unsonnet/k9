from decimal import Decimal
from typing import Iterable

from k9.providers.base import BaseProvider, GrantSpec, apimethod
from k9.providers.database import DatabaseProvider, DatabaseTypes
from k9.providers.location import LocationProvider as _LocationProvider
from k9.shared.config import is_set, missing, settings
from k9.types.common import ResourceID, SubresourceID
from pydantic import BaseModel

__all__ = [
    "LocationProvider",
]


class Address(BaseModel, frozen=True):
    street: str
    city: str
    state: str
    zip: str


class Coordinates(BaseModel, frozen=True):
    lat: Decimal
    lng: Decimal


class Location(BaseModel, frozen=True):
    id: SubresourceID
    scope: ResourceID | None
    address: Address
    geo: Coordinates


class LocationProvider(BaseProvider):
    _db: DatabaseProvider
    _loc: _LocationProvider

    def __init__(
        self,
        *,
        region: str | None = None,
        table: str | None = None,
    ) -> None:
        region = region or settings.aws_region
        # dynamodb
        self._db = DatabaseProvider(
            region=region,
            table=table or settings.dynamodb_table,
        )
        # geo-places
        self._loc = _LocationProvider(
            region=region,
        )

    @property
    def permissions(self) -> Iterable[GrantSpec]:
        yield from self._db.permissions
        yield from self._loc.permissions

    # ──── Public Methods ────

    @apimethod
    def create_location(
        self,
        *,
        id: ResourceID,
        sid: SubresourceID,
        scope: ResourceID | None,
        street: str,
        city: str,
        state: str,
        zip: str,
    ) -> Location:
        lat, lng = self._loc.geocode(street, city, state, zip)
        self._db.create_item(
            f"companies/{id}/locations/{sid}",
            id=sid,
            scope=scope,
            address=dict(street=street, city=city, state=state, zip=zip),
            geo=dict(lat=lat, lng=lng),
        )
        return self.read_location(id=id, sid=sid)

    @apimethod
    def read_location(
        self,
        *,
        id: ResourceID,
        sid: SubresourceID,
    ) -> Location:
        return Location.model_validate(
            self._db.read_item(f"companies/{id}/locations/{sid}"),
        )

    @apimethod
    def update_location(
        self,
        *,
        id: ResourceID,
        sid: SubresourceID,
        scope: ResourceID | None | missing,
    ) -> Location:
        attrs: dict[str, DatabaseTypes] = {}
        if is_set(scope):
            attrs["scope"] = scope
        self._db.update_item(f"companies/{id}/locations/{sid}", **attrs)
        return self.read_location(id=id, sid=sid)

    @apimethod
    def delete_location(
        self,
        *,
        id: ResourceID,
        sid: SubresourceID,
    ) -> None:
        self._db.delete_item(f"companies/{id}/locations/{sid}")
        return None
