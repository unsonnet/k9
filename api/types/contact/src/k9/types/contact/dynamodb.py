from typing import TYPE_CHECKING, Literal, Self

from k9.types.base import Partial, ResourceModel
from k9.types.common import DateID, ResourceID, S3Url, missing
from pydantic import EmailStr
from pydantic_extra_types.phone_numbers import PhoneNumber

__all__ = [
    "Contact",
    "EmailStr",
    "Industry",
    "Job",
    "PhoneNumber",
]


class Job(ResourceModel, frozen=True):
    id: DateID
    scope: ResourceID | None
    company: ResourceID | None
    title: str
    email: EmailStr | None
    phone: PhoneNumber | None

    # BEGIN GENERATED PARTIAL SIGNATURE
    if TYPE_CHECKING:

        @classmethod
        def partial(
            cls,
            *,
            id: DateID | missing = ...,
            scope: ResourceID | None | missing = ...,
            company: ResourceID | None | missing = ...,
            title: str | missing = ...,
            email: EmailStr | None | missing = ...,
            phone: PhoneNumber | None | missing = ...,
        ) -> Partial[Self]: ...
    # END GENERATED PARTIAL SIGNATURE


type Industry = Literal["insurance", "manufacturing", "retail"]


class Contact(ResourceModel, frozen=True):
    id: ResourceID
    scope: ResourceID | None
    type: Industry
    name: str
    picture: S3Url
    email: EmailStr | None
    phone: PhoneNumber | None

    # BEGIN GENERATED PARTIAL SIGNATURE
    if TYPE_CHECKING:

        @classmethod
        def partial(
            cls,
            *,
            id: ResourceID | missing = ...,
            scope: ResourceID | None | missing = ...,
            type: Industry | missing = ...,
            name: str | missing = ...,
            picture: S3Url | missing = ...,
            email: EmailStr | None | missing = ...,
            phone: PhoneNumber | None | missing = ...,
        ) -> Partial[Self]: ...
    # END GENERATED PARTIAL SIGNATURE
