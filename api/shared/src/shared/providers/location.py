from collections.abc import Iterable
from decimal import Decimal

import boto3
from types_boto3_geo_places import LocationServicePlacesV2Client

from ..config import GrantSpec
from ..errors import DomainForbidden, DomainNotFound, DomainRateLimited
from . import BaseProvider, ExceptionMap, apimethod

__all__ = [
    "LocationProvider",
]


class LocationProvider(BaseProvider):
    _loc: LocationServicePlacesV2Client

    def __init__(
        self,
        *,
        region: str,
    ) -> None:
        self._loc = boto3.client("geo-places", region_name=region)

    @property
    def permissions(self) -> Iterable[GrantSpec]:
        yield GrantSpec(
            actions=("geo-places:Geocode",),
            resources=("*",),
        )

    @property
    def exception_map(self) -> ExceptionMap:
        lx = self._loc.exceptions
        return {
            DomainForbidden: [
                lx.AccessDeniedException,
            ],
            DomainRateLimited: [
                lx.ThrottlingException,
            ],
        }

    # ──── Public Methods ────

    @apimethod
    def geocode(
        self, street: str, city: str, state: str, zip: str
    ) -> tuple[Decimal, Decimal]:
        response = self._loc.geocode(QueryText=f"{street}, {city}, {state} {zip} USA")
        items = response.get("ResultItems", [])
        if not items or "Position" not in items[0]:
            raise DomainNotFound()
        lng, lat = items[0]["Position"]
        return Decimal(str(lat)), Decimal(str(lng))
