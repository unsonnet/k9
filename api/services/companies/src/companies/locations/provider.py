from typing import Iterable

from shared.config import settings
from shared.providers import BaseProvider, GrantSpec, apimethod
from shared.providers.database import DatabaseProvider
from shared.providers.location import LocationProvider

from .models import Location

__all__ = [
    "CompanyLocationProvider",
]


class CompanyLocationProvider(BaseProvider):
    _db: DatabaseProvider
    _loc: LocationProvider

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
        self._loc = LocationProvider(
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
        id: str,
        sid: str,
        street: str,
        city: str,
        state: str,
        zip: str,
    ) -> Location:
        lat, lon = self._loc.geocode(street, city, state, zip)
        self._db.create_item(
            type="company.location",
            id=f"{id}.{sid}",
            street=street,
            city=city,
            state=state,
            zip=zip,
            lat=lat,
            lon=lon,
        )
        return Location.model_validate(
            self._db.read_item(
                type="company.location",
                id=f"{id}.{sid}",
            ),
        )

    @apimethod
    def delete_location(
        self,
        *,
        id: str,
        sid: str,
    ) -> None:
        self._db.delete_item(
            type="company.location",
            id=f"{id}.{sid}",
        )
        return None
