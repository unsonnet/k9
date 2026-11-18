from typing import Iterable

from k9.providers.base import BaseProvider, GrantSpec, apimethod
from k9.providers.database import DatabaseProvider
from k9.providers.location import LocationProvider as GeoProvider
from k9.shared.config import settings
from k9.types.common import ResourceID, SubresourceID, missing
from k9.types.company import Address, Coordinates, Location

__all__ = [
    "LocationProvider",
]


class LocationProvider(BaseProvider):
    _db: DatabaseProvider
    _geo: GeoProvider

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
        self._geo = GeoProvider(
            region=region,
        )

    @property
    def permissions(self) -> Iterable[GrantSpec]:
        yield from self._db.permissions
        yield from self._geo.permissions

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
        lat, lng = self._geo.geocode(street, city, state, zip)
        self._db.create_item(
            f"companies/{id}/locations/{sid}",
            Location(
                id=sid,
                scope=scope,
                address=Address(
                    street=street,
                    city=city,
                    state=state,
                    zip=zip,
                ),
                geo=Coordinates(
                    lat=lat,
                    lng=lng,
                ),
            ),
        )
        return self.read_location(id=id, sid=sid)

    @apimethod
    def read_location(
        self,
        *,
        id: ResourceID,
        sid: SubresourceID,
    ) -> Location:
        return self._db.read_item(
            f"companies/{id}/locations/{sid}",
            Location,
        )

    @apimethod
    def update_location(
        self,
        *,
        id: ResourceID,
        sid: SubresourceID,
        scope: ResourceID | None | missing,
    ) -> Location:
        self._db.update_item(
            f"companies/{id}/locations/{sid}",
            Location.partial(
                scope=scope,
            ),
        )
        return self.read_location(id=id, sid=sid)

    @apimethod
    def delete_location(
        self,
        *,
        id: ResourceID,
        sid: SubresourceID,
    ) -> None:
        return self._db.delete_item(f"companies/{id}/locations/{sid}")
