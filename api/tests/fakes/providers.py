from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Mapping, Sequence
from uuid import UUID, uuid4

from pydantic import AnyUrl, TypeAdapter

from src.models.auth import AuthChallenge, AuthTokens
from src.models.common import (
    PasswordStr,
    PrefValueStr,
    RoleStr,
    SessionStr,
    TokenStr,
    UsernameStr,
)
from src.models.product import (
    Image as ModelImage,
    Name,
    Product as ModelProduct,
    ProductSummary,
    StoredFormat,
    StoredImage,
    StoredProduct,
    StoredVendor,
)
from src.models.report import StoredReport, StoredReportSummary
from src.models.search import SearchHit, SearchRequest, SearchResult
from src.models.user import StoredProfile
from src.services.errors import (
    DomainConflict,
    DomainForbidden,
    DomainNotFound,
    DomainUnauthorized,
)
from src.services.errors import DomainExpiredToken
from src.services.auth.provider import AuthProvider
from src.services.user.provider import UserDBProvider
from src.services.product.provider import (
    EmbeddingIndexProvider,
    ImageDBProvider,
    ProductDBProvider,
)
from src.services.report.provider import (
    ProductResolver,
    ReportDBProvider,
    UserResolver,
)
from src.services.search.provider import (
    ProductSummaryProvider,
    SearchProvider,
)


# ─────────────────────────────────────────────────────────────────────────────
# In-memory store used by fakes
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class FakeStore:
    users: dict[UUID, StoredProfile] = field(default_factory=dict)
    products: dict[UUID, StoredProduct] = field(default_factory=dict)
    reports: dict[UUID, StoredReport] = field(default_factory=dict)


def _now() -> datetime:
    return datetime.now(timezone.utc)


_URL_ADAPTER = TypeAdapter(AnyUrl)


def _anyurl(url: str) -> AnyUrl:
    val = _URL_ADAPTER.validate_python(url)
    return val


# ─────────────────────────────────────────────────────────────────────────────
# Auth fakes
# ─────────────────────────────────────────────────────────────────────────────
class FakeAuthProvider(AuthProvider):
    def __init__(self) -> None:
        self.valid_user = UUID("00000000-0000-0000-0000-000000000001")

    def start_password_reset(self, username: UsernameStr) -> None:  # type: ignore[override]
        if username == "missing":
            raise DomainNotFound()

    def authenticate(
        self, username: UsernameStr, password: PasswordStr
    ) -> AuthTokens | AuthChallenge:  # type: ignore[override]
        if password == "bad":
            raise DomainUnauthorized()
        if username == "challenge":
            # session must satisfy SessionStr min_length=10
            return AuthChallenge(username=username, session="session-abc123")
        return AuthTokens(
            user=self.valid_user,
            # tokens must satisfy TokenStr min_length=16
            access_token="access-token-123456",
            refresh_token="refresh-token-123456",
            expires_in=3600,
        )

    def logout(self, bearer_token: TokenStr) -> None:  # type: ignore[override]
        if bearer_token == "bad":
            raise DomainUnauthorized()

    def refresh(self, username: UsernameStr, refresh_token: TokenStr) -> AuthTokens:  # type: ignore[override]
        if username == "missing":
            raise DomainNotFound()
        if str(refresh_token).endswith("expired") or str(refresh_token).endswith("bad"):
            # simulate expired/invalid
            raise DomainExpiredToken("expired")
        return AuthTokens(
            user=self.valid_user,
            access_token="access-token-456789",
            refresh_token="refresh-token-456789",
            expires_in=3600,
        )

    def reset_password(
        self, username: UsernameStr, session: SessionStr, new_password: PasswordStr
    ) -> None:  # type: ignore[override]
        if username == "missing":
            raise DomainNotFound()
        if str(session).endswith("expired"):
            raise DomainExpiredToken("expired")


# ─────────────────────────────────────────────────────────────────────────────
# User fakes
# ─────────────────────────────────────────────────────────────────────────────
class FakeUserDBProvider(UserDBProvider):
    def __init__(self, store: FakeStore) -> None:
        self.store = store

    def get_user(self, ctx, *, uid: UUID) -> StoredProfile:  # type: ignore[override]
        if uid not in self.store.users:
            raise DomainNotFound()
        return self.store.users[uid]

    def post_user(
        self,
        ctx,
        *,
        username: UsernameStr,
        role: RoleStr,
        preferences: Mapping[str, PrefValueStr] | None,
    ) -> StoredProfile:  # type: ignore[override]
        # conflict if username exists
        if any(u.username == username for u in self.store.users.values()):
            raise DomainConflict()
        uid = uuid4()
        user = StoredProfile(
            id=uid,
            username=username,
            role=role,
            preferences=dict(preferences or {}),
            createdAt=_now(),
        )
        self.store.users[uid] = user
        return user

    def put_user(self, ctx, *, user: StoredProfile) -> StoredProfile:  # type: ignore[override]
        if user.id not in self.store.users:
            raise DomainNotFound()
        self.store.users[user.id] = user
        return user

    def delete_user(self, ctx, *, uid: UUID) -> None:  # type: ignore[override]
        if uid not in self.store.users:
            raise DomainNotFound()
        del self.store.users[uid]

    def list_users(self, ctx, *, limit: int | None, next_token: str | None):  # type: ignore[override]
        from src.services.user.provider import ListUsersResult

        all_users = list(self.store.users.values())
        return ListUsersResult(total=len(all_users), users=all_users, nextToken=None)

    def update_password(
        self, ctx, *, uid: UUID, current_password: str, new_password: str
    ) -> None:  # type: ignore[override]
        if uid not in self.store.users:
            raise DomainNotFound()
        if current_password == "wrong":
            raise DomainForbidden()


# ─────────────────────────────────────────────────────────────────────────────
# Product fakes
# ─────────────────────────────────────────────────────────────────────────────
class FakeProductDBProvider(ProductDBProvider):
    def __init__(self, store: FakeStore) -> None:
        self.store = store

    def get_product(self, ctx, *, pid: UUID, embeddings: bool = False) -> StoredProduct:  # type: ignore[override]
        if pid not in self.store.products:
            raise DomainNotFound()
        return self.store.products[pid]

    def post_product(
        self, ctx, *, name: Name, category: Mapping[str, str]
    ) -> StoredProduct:  # type: ignore[override]
        pid = uuid4()
        prod = StoredProduct(
            id=pid,
            name=name,
            category=dict(category),
            formats=[],
            images=[],
            createdAt=_now(),
        )
        self.store.products[pid] = prod
        return prod

    def put_product(self, ctx, *, product: StoredProduct) -> StoredProduct:  # type: ignore[override]
        if product.id not in self.store.products:
            raise DomainNotFound()
        self.store.products[product.id] = product
        return product

    def delete_product(self, ctx, *, pid: UUID) -> None:  # type: ignore[override]
        if pid not in self.store.products:
            raise DomainNotFound()
        del self.store.products[pid]


class FakeImageDBProvider(ImageDBProvider):
    def __init__(self, store: FakeStore) -> None:
        self.store = store
        self.meta: dict[tuple[UUID, UUID], dict[str, str | None]] = {}

    def post_image(
        self,
        ctx,
        *,
        pid: UUID,
        original_bytes: bytes,
        transformed_bytes: bytes,
        metadata: Mapping[str, str | None],
    ) -> UUID:  # type: ignore[override]
        iid = uuid4()
        prod = self.store.products.get(pid)
        if not prod:
            raise DomainNotFound()
        stored = StoredImage(id=iid, createdAt=_now(), localEmbeddings=None)
        prod.images = [*prod.images, stored]
        self.meta[(pid, iid)] = dict(metadata)
        return iid

    def put_image_metadata(
        self, ctx, *, pid: UUID, iid: UUID, metadata: Mapping[str, str | None]
    ) -> None:  # type: ignore[override]
        key = (pid, iid)
        if key not in self.meta:
            self.meta[key] = {}
        self.meta[key].update(metadata)

    def get_url(self, ctx, *, pid: UUID, iid: UUID, kind: str) -> AnyUrl:  # type: ignore[override]
        return _anyurl(f"https://example.com/{pid}/{iid}/{kind}.jpg")

    def delete(self, ctx, *, pid: UUID, iid: UUID) -> None:  # type: ignore[override]
        prod = self.store.products.get(pid)
        if not prod:
            raise DomainNotFound()
        prod.images = [i for i in prod.images if i.id != iid]
        self.meta.pop((pid, iid), None)


class FakeEmbeddingIndexProvider(EmbeddingIndexProvider):
    def upsert_product_embedding(self, *_, **__): ...  # type: ignore[override]

    def delete_product_embedding(self, *_, **__): ...  # type: ignore[override]

    def upsert_image_local_embeddings(self, *_, **__): ...  # type: ignore[override]

    def delete_image_local_embeddings(self, *_, **__): ...  # type: ignore[override]


# ─────────────────────────────────────────────────────────────────────────────
# Report fakes
# ─────────────────────────────────────────────────────────────────────────────
class FakeReportDBProvider(ReportDBProvider):
    def __init__(self, store: FakeStore) -> None:
        self.store = store

    def get_report(self, ctx, *, rid: UUID) -> StoredReport:  # type: ignore[override]
        if rid not in self.store.reports:
            raise DomainNotFound()
        return self.store.reports[rid]

    def post_report(
        self, ctx, *, author: UUID, title: str, reference: UUID
    ) -> StoredReport:  # type: ignore[override]
        rid = uuid4()
        rep = StoredReport(
            id=rid,
            author=author,
            title=title,
            createdAt=_now(),
            referenceId=reference,
            favoriteIds=[],
        )
        self.store.reports[rid] = rep
        return rep

    def put_report(self, ctx, *, report: StoredReport) -> StoredReport:  # type: ignore[override]
        if report.id not in self.store.reports:
            raise DomainNotFound()
        self.store.reports[report.id] = report
        return report

    def delete_report(self, ctx, *, rid: UUID) -> None:  # type: ignore[override]
        if rid not in self.store.reports:
            raise DomainNotFound()
        del self.store.reports[rid]

    def list_reports(
        self, ctx, *, limit: int | None, next_token: str | None, everyone: bool | None
    ):
        from src.services.report.provider import ListReportsResult

        summaries: list[StoredReportSummary] = []
        for r in self.store.reports.values():
            summaries.append(
                StoredReportSummary(
                    id=r.id,
                    author=r.author,
                    title=r.title,
                    createdAt=r.createdAt,
                    referenceId=r.referenceId,
                )
            )
        return ListReportsResult(
            total=len(summaries), reports=summaries, nextToken=None
        )


class FakeProductResolver(ProductResolver):
    def __init__(self, store: FakeStore) -> None:
        self.store = store

    def get_product(self, ctx, *, pid: UUID) -> ModelProduct:  # type: ignore[override]
        if pid not in self.store.products:
            raise DomainNotFound()
        sp = self.store.products[pid]
        from src.models.product import Format as ModelFormat, Vendor as ModelVendor

        return ModelProduct(
            id=sp.id,
            name=sp.name,
            category=sp.category,
            formats=[
                ModelFormat(
                    id=f.id,
                    aspect=f.aspect,
                    length=f.length,
                    width=f.width,
                    thickness=f.thickness,
                    vendors=[
                        ModelVendor(
                            id=vv.id,
                            sku=vv.sku,
                            store=vv.store,
                            name=vv.name,
                            price=vv.price,
                            discontinued=vv.discontinued,
                            url=vv.url,
                        )
                        for vv in f.vendors
                    ],
                )
                for f in sp.formats
            ],
            images=[
                ModelImage(
                    id=i.id,
                    url=_anyurl(f"https://example.com/{pid}/{i.id}/transformed.jpg"),
                )
                for i in sp.images
            ],
        )

    def get_summary(self, ctx, *, pid: UUID) -> ProductSummary:  # type: ignore[override]
        if pid not in self.store.products:
            raise DomainNotFound()
        sp = self.store.products[pid]
        img = sp.images[0] if sp.images else StoredImage(id=uuid4(), createdAt=_now())
        return ProductSummary(
            id=sp.id,
            name=sp.name,
            image=ModelImage(
                id=img.id, url=_anyurl(f"https://example.com/{pid}/{img.id}/thumb.jpg")
            ),
        )


class FakeUserResolver(UserResolver):
    def __init__(self, user_id: UUID | None = None) -> None:
        self.user_id = user_id or UUID("00000000-0000-0000-0000-00000000cafe")

    def get_user_id(self, ctx) -> UUID:  # type: ignore[override]
        return self.user_id


# ─────────────────────────────────────────────────────────────────────────────
# Search fakes
# ─────────────────────────────────────────────────────────────────────────────
class FakeSearchProvider(SearchProvider):
    def __init__(self, hits: Sequence[UUID] | None = None) -> None:
        self.hits = list(hits or [])

    def search(
        self,
        ctx,
        *,
        query: SearchRequest,
        limit: int | None,
        next_token: str | None,
        partial: bool | None,
    ) -> SearchResult:  # type: ignore[override]
        return SearchResult(
            total=len(self.hits),
            hits=[SearchHit(id=h, score=90) for h in self.hits],
            nextToken=None,
        )


class FakeProductSummaryProvider(ProductSummaryProvider):
    def __init__(self, store: FakeStore) -> None:
        self.store = store

    def get_summary(self, ctx, *, pid: UUID) -> ProductSummary:  # type: ignore[override]
        if pid not in self.store.products:
            raise DomainNotFound()
        sp = self.store.products[pid]
        img = sp.images[0] if sp.images else StoredImage(id=uuid4(), createdAt=_now())
        return ProductSummary(
            id=sp.id,
            name=sp.name,
            image=ModelImage(
                id=img.id, url=_anyurl(f"https://example.com/{pid}/{img.id}/thumb.jpg")
            ),
        )
