#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Final, NoReturn
from uuid import UUID
from pydantic import AnyUrl

from models.common import CategoryMap
from models.product import (
    ProductName,
    StoredProduct,
    ImageMask,
    HomographyMatrix,
    LocalEmbeddings,
    GlobalEmbedding,
)
from utils.errors import DomainInvariantViolation


# ──────────────────────────────────────────────────────────────────────────────
# Product Provider
# ──────────────────────────────────────────────────────────────────────────────
class ProductDBProvider(ABC):
    """Manage product data contracts for backends."""

    @abstractmethod
    def get_product(self, *, pid: UUID, embeddings: bool = False) -> StoredProduct:
        """Retrieve product by id."""
        ...

    @abstractmethod
    def post_product(
        self,
        *,
        name: ProductName,
        category: CategoryMap,
    ) -> StoredProduct:
        """Create product record."""
        ...

    @abstractmethod
    def put_product(self, *, product: StoredProduct) -> StoredProduct:
        """Replace product record."""
        ...

    @abstractmethod
    def delete_product(self, *, pid: UUID) -> None:
        """Delete product record."""
        ...


# ──────────────────────────────────────────────────────────────────────────────
# Disabled Provider
# ──────────────────────────────────────────────────────────────────────────────
class _NoopProductDBProvider(ProductDBProvider):
    """Manage product operations as a disabled provider."""

    _MSG: Final = "Failed to perform product operation."

    def _raise(self) -> NoReturn:
        raise DomainInvariantViolation(self._MSG)

    def get_product(self, *_, **__) -> StoredProduct:
        self._raise()

    def post_product(self, *_, **__) -> StoredProduct:
        self._raise()

    def put_product(self, *_, **__) -> StoredProduct:
        self._raise()

    def delete_product(self, *_, **__) -> None:
        self._raise()


# ──────────────────────────────────────────────────────────────────────────────
# Image Provider
# ──────────────────────────────────────────────────────────────────────────────
class ImageDBProvider(ABC):
    """Manage image storage, transformation, metadata, and embeddings."""

    @abstractmethod
    def post_image(
        self,
        *,
        pid: UUID,
        image: bytes,
        mask: ImageMask | None,
        homography: HomographyMatrix | None,
    ) -> tuple[UUID, LocalEmbeddings, GlobalEmbedding]:
        """
        Store original image, apply optional mask/homography to produce transformed
        variant, and compute embeddings.

        Returns:
            (iid, local_vectors, global_vector)
        """
        ...

    @abstractmethod
    def put_image(
        self,
        *,
        pid: UUID,
        iid: UUID,
        mask: ImageMask | None,
        homography: HomographyMatrix | None,
    ) -> tuple[LocalEmbeddings, GlobalEmbedding]:
        """
        Update image transformation metadata (mask/homography) and recompute
        embeddings for the image and product.

        Returns:
            (local_vectors, global_vector)
        """
        ...

    @abstractmethod
    def get_url(self, *, pid: UUID, iid: UUID, original: bool) -> AnyUrl:
        """Retrieve a URL for the original or transformed image."""
        ...

    @abstractmethod
    def delete(self, *, pid: UUID, iid: UUID) -> None:
        """Delete image and any derived artifacts."""
        ...


# ──────────────────────────────────────────────────────────────────────────────
# Disabled Provider
# ──────────────────────────────────────────────────────────────────────────────
class _NoopImageDBProvider(ImageDBProvider):
    """Manage image operations as a disabled provider."""

    _MSG: Final = "Failed to perform image operation."

    def _raise(self) -> NoReturn:
        raise DomainInvariantViolation(self._MSG)

    def post_image(self, *_, **__) -> tuple[UUID, LocalEmbeddings, GlobalEmbedding]:
        self._raise()

    def put_image(self, *_, **__) -> tuple[LocalEmbeddings, GlobalEmbedding]:
        self._raise()

    def get_url(self, *_, **__) -> AnyUrl:
        self._raise()

    def delete(self, *_, **__) -> None:
        self._raise()
