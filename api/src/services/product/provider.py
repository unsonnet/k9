#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Mapping, Sequence
from uuid import UUID
from pydantic import AnyUrl

# ──────────────────────────────────────────────────────────────────────────────
from models.auth import AuthContext
from models.common import CategoryMap
from models.product import (
    Name,
    StoredProduct,
)


# ──────────────────────────────────────────────────────────────────────────────
# Provider Interfaces
# ──────────────────────────────────────────────────────────────────────────────
class ProductDBProvider(ABC):
    """Backend contract for product persistence."""

    @abstractmethod
    def get_product(
        self, ctx: AuthContext, *, pid: UUID, embeddings: bool = False
    ) -> StoredProduct: ...

    @abstractmethod
    def post_product(
        self,
        ctx: AuthContext,
        *,
        name: Name,
        category: CategoryMap,
    ) -> StoredProduct: ...

    @abstractmethod
    def put_product(
        self, ctx: AuthContext, *, product: StoredProduct
    ) -> StoredProduct: ...

    @abstractmethod
    def delete_product(self, ctx: AuthContext, *, pid: UUID) -> None: ...


class ImageDBProvider(ABC):
    """Backend contract for image persistence and metadata."""

    @abstractmethod
    def post_image(
        self,
        ctx: AuthContext,
        *,
        pid: UUID,
        original_bytes: bytes,
        transformed_bytes: bytes,
        metadata: Mapping[str, str | None],
    ) -> UUID: ...

    @abstractmethod
    def put_image_metadata(
        self,
        ctx: AuthContext,
        *,
        pid: UUID,
        iid: UUID,
        metadata: Mapping[str, str | None],
    ) -> None: ...

    @abstractmethod
    def get_url(
        self, ctx: AuthContext, *, pid: UUID, iid: UUID, kind: str
    ) -> AnyUrl: ...

    @abstractmethod
    def delete(self, ctx: AuthContext, *, pid: UUID, iid: UUID) -> None: ...


class EmbeddingIndexProvider(ABC):
    @abstractmethod
    def upsert_product_embedding(
        self, ctx: AuthContext, *, pid: UUID, vector: Sequence[float]
    ) -> None: ...

    @abstractmethod
    def delete_product_embedding(self, ctx: AuthContext, *, pid: UUID) -> None: ...

    @abstractmethod
    def upsert_image_local_embeddings(
        self,
        ctx: AuthContext,
        *,
        pid: UUID,
        iid: UUID,
        vectors: Sequence[Sequence[float]],
    ) -> None: ...

    @abstractmethod
    def delete_image_local_embeddings(
        self, ctx: AuthContext, *, pid: UUID, iid: UUID
    ) -> None: ...


class NoopEmbeddingIndexProvider(EmbeddingIndexProvider):
    def upsert_product_embedding(self, *_, **__): ...
    def delete_product_embedding(self, *_, **__): ...
    def upsert_image_local_embeddings(self, *_, **__): ...
    def delete_image_local_embeddings(self, *_, **__): ...


# Default underscored no-ops for DB and Images
class _NoopProductDB(ProductDBProvider):  # pragma: no cover - placeholder
    def get_product(self, *_, **__) -> StoredProduct:  # type: ignore[override]
        raise NotImplementedError("ProductDBProvider not configured")

    def post_product(self, *_, **__) -> StoredProduct:  # type: ignore[override]
        raise NotImplementedError("ProductDBProvider not configured")

    def put_product(self, *_, **__) -> StoredProduct:  # type: ignore[override]
        raise NotImplementedError("ProductDBProvider not configured")

    def delete_product(self, *_, **__) -> None:  # type: ignore[override]
        raise NotImplementedError("ProductDBProvider not configured")


class _NoopImageDB(ImageDBProvider):  # pragma: no cover - placeholder
    def post_image(self, *_, **__) -> UUID:  # type: ignore[override]
        raise NotImplementedError("ImageDBProvider not configured")

    def put_image_metadata(self, *_, **__) -> None:  # type: ignore[override]
        raise NotImplementedError("ImageDBProvider not configured")

    def get_url(self, *_, **__) -> AnyUrl:  # type: ignore[override]
        raise NotImplementedError("ImageDBProvider not configured")

    def delete(self, *_, **__) -> None:  # type: ignore[override]
        raise NotImplementedError("ImageDBProvider not configured")
