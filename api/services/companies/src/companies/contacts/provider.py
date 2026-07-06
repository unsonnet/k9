from typing import Iterable, Protocol

from shared.config import GrantSpec, missing

from .models import Contact, Page

__all__ = [
    "ContactProvider",
    "AWSContactProvider",
]


class ContactProvider(Protocol):
    @property
    def permissions(self) -> Iterable[GrantSpec]: ...

    def list_contacts(
        self,
        *,
        id: str,
        limit: int,
        cursor: str | missing,
    ) -> Page: ...

    def create_contact(
        self,
        *,
        id: str,
        sid: str,
        name: str,
        title: str | None,
        email: str | None,
        phone: str | None,
    ) -> Contact: ...

    def read_contact(
        self,
        *,
        id: str,
        sid: str,
    ) -> Contact: ...

    def update_contact(
        self,
        *,
        id: str,
        sid: str,
        name: str | missing,
        title: str | None | missing,
        email: str | None | missing,
        phone: str | None | missing,
    ) -> Contact: ...

    def delete_contact(
        self,
        *,
        id: str,
        sid: str,
    ) -> None: ...


# ──── AWS Contact Provider ────────────────────────────────────────────────────────────


class AWSContactProvider:
    @property
    def permissions(self) -> Iterable[GrantSpec]:
        return []

    def list_contacts(
        self,
        *,
        id: str,
        limit: int,
        cursor: str | missing,
    ) -> Page:
        raise NotImplementedError()

    def create_contact(
        self,
        *,
        id: str,
        sid: str,
        name: str,
        title: str | None,
        email: str | None,
        phone: str | None,
    ) -> Contact:
        raise NotImplementedError()

    def read_contact(
        self,
        *,
        id: str,
        sid: str,
    ) -> Contact:
        raise NotImplementedError()

    def update_contact(
        self,
        *,
        id: str,
        sid: str,
        name: str | missing,
        title: str | None | missing,
        email: str | None | missing,
        phone: str | None | missing,
    ) -> Contact:
        raise NotImplementedError()

    def delete_contact(
        self,
        *,
        id: str,
        sid: str,
    ) -> None:
        raise NotImplementedError()
