#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Product domain models - Business entities with ML embeddings and storage."""

from __future__ import annotations

from typing import Any, Optional, Sequence
from uuid import UUID

import numpy as np
from numpy.typing import NDArray
from pydantic import AnyUrl, ConfigDict, field_serializer, field_validator

from ..shared.base import DomainModel, StorageModel, TimeStamped
from ..shared.types import CategoryMap, NonEmptyStr
from ..shared.values import Currency, Dimension, Name

# ──────────────────────────────────────────────────────────────────────────────
# Type Aliases for ML Features
# ──────────────────────────────────────────────────────────────────────────────

ImageMask = NDArray[np.bool_]
"""2D binary mask for image regions."""

HomographyMatrix = NDArray[np.float64]
"""3x3 homography transformation matrix."""

LocalEmbeddings = NDArray[np.float32]
"""2D array of per-image dense local feature vectors."""

GlobalEmbedding = NDArray[np.float32]
"""1D array representing product-level global features."""


# ──────────────────────────────────────────────────────────────────────────────
# Core Domain Entities
# ──────────────────────────────────────────────────────────────────────────────


class VendorInfo(DomainModel):
    """Vendor information value object."""

    id: UUID
    sku: NonEmptyStr
    store: NonEmptyStr
    name: NonEmptyStr
    price: Optional[Currency] = None
    discontinued: Optional[bool] = None
    url: Optional[AnyUrl] = None


class VendorEntity(StorageModel, TimeStamped):
    """Vendor entity with persistence metadata."""

    id: UUID
    sku: NonEmptyStr
    store: NonEmptyStr
    name: NonEmptyStr
    price: Optional[Currency] = None
    discontinued: Optional[bool] = None
    url: Optional[AnyUrl] = None


class FormatInfo(DomainModel):
    """Product format information."""

    id: UUID
    aspect: NonEmptyStr
    length: Optional[Dimension] = None
    width: Optional[Dimension] = None
    thickness: Optional[Dimension] = None
    vendors: Sequence[VendorInfo] = ()


class FormatEntity(StorageModel, TimeStamped):
    """Format entity with persistence metadata."""

    id: UUID
    aspect: NonEmptyStr
    length: Optional[Dimension] = None
    width: Optional[Dimension] = None
    thickness: Optional[Dimension] = None
    vendors: Sequence[VendorEntity] = ()


class ImageInfo(DomainModel):
    """Basic image information for API exposure."""

    id: UUID
    url: AnyUrl


class ImageEntity(StorageModel, TimeStamped):
    """Image entity with ML embeddings for internal use."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: UUID
    local_embeddings: LocalEmbeddings

    @field_validator("local_embeddings", mode="before")
    @classmethod
    def _validate_local_embeddings(cls, v: Any) -> LocalEmbeddings:
        """Validate and convert local embeddings to proper 2D float32 array."""
        if v is None:
            return np.zeros((0, 0), dtype=np.float32)
        arr = np.asarray(v, dtype=np.float32)
        if arr.ndim != 2:
            raise ValueError("local_embeddings must be 2D array")
        return arr

    @field_serializer("local_embeddings")
    def _serialize_local_embeddings(
        self, v: LocalEmbeddings, _info
    ) -> list[list[float]]:
        """Serialize embeddings to nested lists for JSON."""
        return v.tolist()


class ProductSummary(DomainModel):
    """Product summary for listings and references."""

    id: UUID
    name: Name
    image: ImageInfo


class Product(DomainModel):
    """Complete product information for API responses."""

    id: UUID
    name: Name
    category: CategoryMap
    formats: Sequence[FormatInfo]
    images: Sequence[ImageInfo]


class ProductEntity(StorageModel, TimeStamped):
    """Product entity with ML embeddings and full persistence metadata."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: UUID
    name: Name
    category: CategoryMap
    formats: Sequence[FormatEntity]
    images: Sequence[ImageEntity]
    global_embedding: GlobalEmbedding

    @field_validator("global_embedding", mode="before")
    @classmethod
    def _validate_global_embedding(cls, v: Any) -> GlobalEmbedding:
        """Validate and convert global embedding to proper 1D float32 array."""
        if v is None:
            return np.zeros((0,), dtype=np.float32)
        arr = np.asarray(v, dtype=np.float32)
        if arr.ndim != 1:
            raise ValueError("global_embedding must be 1D array")
        return arr

    @field_serializer("global_embedding")
    def _serialize_global_embedding(self, v: GlobalEmbedding, _info) -> list[float]:
        """Serialize global embedding to list for JSON."""
        return v.tolist()
