from __future__ import annotations

import base64
import json
from typing import Iterator
from uuid import UUID, uuid4

import pytest

from tests.fakes.providers import (
    FakeAuthProvider,
    FakeEmbeddingIndexProvider,
    FakeImageDBProvider,
    FakeProductDBProvider,
    FakeProductResolver,
    FakeProductSummaryProvider,
    FakeReportDBProvider,
    FakeStore,
    FakeUserDBProvider,
    FakeUserResolver,
)


@pytest.fixture()
def store() -> FakeStore:
    return FakeStore()


@pytest.fixture()
def auth_headers() -> dict[str, str]:
    return {"Authorization": "Bearer test-token-1234567890"}


@pytest.fixture(autouse=True)
def patch_providers(
    store: FakeStore, monkeypatch: pytest.MonkeyPatch
) -> Iterator[None]:
    """Autouse fixture to inject fake providers into handler-level service instances.

    This keeps tests exercising the handler + service mapping while avoiding real backends.
    """
    # Auth
    from src.handlers import auth as h_auth

    h_auth.svc.provider = FakeAuthProvider()

    # User
    from src.handlers import user as h_user

    h_user.svc.provider = FakeUserDBProvider(store)

    # Product
    from src.handlers import product as h_product

    h_product.svc.db = FakeProductDBProvider(store)
    h_product.svc.images = FakeImageDBProvider(store)
    h_product.svc.embed = FakeEmbeddingIndexProvider()

    # Report
    from src.handlers import report as h_report

    h_report.svc.provider = FakeReportDBProvider(store)
    h_report.svc.products = FakeProductResolver(store)
    h_report.svc.users = FakeUserResolver()

    # Search
    from src.handlers import search as h_search
    from tests.fakes.providers import FakeSearchProvider

    h_search.svc.provider = FakeSearchProvider([])
    h_search.svc.products = FakeProductSummaryProvider(store)

    yield


@pytest.fixture()
def seed_product(store: FakeStore, auth_headers: dict[str, str]):
    """Create and return a stored product id for tests that need an existing product."""
    db = FakeProductDBProvider(store)
    from src.models.product import Name
    from src.models.auth import AuthContext

    prod = db.post_product(
        AuthContext(bearerToken="seed-token-1234567890"),
        name=Name(brand="b", series="s", model="m"),
        category={"type": "tile"},
    )
    return prod.id


@pytest.fixture()
def seed_user(store: FakeStore):
    provider = FakeUserDBProvider(store)
    from src.models.auth import AuthContext

    user = provider.post_user(
        AuthContext(bearerToken="seed-token-1234567890"),
        username="alice",
        role="admin",
        preferences={"theme": "dark"},
    )
    return user.id
