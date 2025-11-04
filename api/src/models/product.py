# models/product.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Mapping, Sequence, Optional, Any
from uuid import UUID

import numpy as np
from numpy.typing import NDArray
from pydantic import BaseModel, AnyUrl, field_validator, field_serializer
from pydantic import ConfigDict

from .common import (
    CategoryMap,
    NonEmptyStr,
    TimeStamped,
)

# ──────────────────────────────────────────────────────────────────────────────
# Type Aliases (provider-level, API-agnostic)
# ──────────────────────────────────────────────────────────────────────────────
ImageMask = NDArray[np.bool_]  # 2d binary mask
HomographyMatrix = NDArray[np.float64]  # 3x3 homography matrix
LocalEmbeddings = NDArray[np.float32]  # 2d per-image dense local vectors
GlobalEmbedding = NDArray[np.float32]  # 1d per-product global vector


# ──────────────────────────────────────────────────────────────────────────────
# Core Shared Models
# ──────────────────────────────────────────────────────────────────────────────
class Dimension(BaseModel):
    model_config = ConfigDict(frozen=True)
    value: int
    unit: NonEmptyStr


class Currency(BaseModel):
    model_config = ConfigDict(frozen=True)
    value: int
    unit: NonEmptyStr


class ProductName(BaseModel):
    """Unified product name schema; all fields optional for create/patch/partial."""

    model_config = ConfigDict(frozen=True)
    brand: Optional[NonEmptyStr] = None
    series: Optional[NonEmptyStr] = None
    model: Optional[NonEmptyStr] = None


# ──────────────────────────────────────────────────────────────────────────────
# Vendor / Format / Product
# ──────────────────────────────────────────────────────────────────────────────
class VendorBase(BaseModel):
    model_config = ConfigDict(frozen=True)
    sku: NonEmptyStr
    store: NonEmptyStr
    name: NonEmptyStr
    price: Optional[Currency] = None
    discontinued: Optional[bool] = None
    url: Optional[AnyUrl] = None


class Vendor(VendorBase):
    id: UUID


class StoredVendor(VendorBase, TimeStamped):
    id: UUID


class FormatBase(BaseModel):
    model_config = ConfigDict(frozen=True)
    aspect: NonEmptyStr
    length: Optional[Dimension] = None
    width: Optional[Dimension] = None
    thickness: Optional[Dimension] = None


class Format(FormatBase):
    id: UUID
    vendors: Sequence[Vendor] = ()


class StoredFormat(FormatBase, TimeStamped):
    id: UUID
    vendors: Sequence[StoredVendor] = ()


class Image(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: UUID
    url: AnyUrl


class StoredImage(TimeStamped):
    # Allow ndarray while keeping strict round-trip via validators/serializers
    model_config = ConfigDict(arbitrary_types_allowed=True)
    id: UUID
    localEmbeddings: LocalEmbeddings

    # ---- NumPy LocalEmbeddings ser/de ----
    @field_validator("localEmbeddings", mode="before")
    @classmethod
    def _as_f32_2d(cls, v: Any) -> LocalEmbeddings:
        if v is None:
            return np.zeros((0, 0), dtype=np.float32)
        a = np.asarray(v, dtype=np.float32)
        if a.ndim != 2:
            raise ValueError("localEmbeddings must be 2D")
        return a

    @field_serializer("localEmbeddings")
    def _dump_local(cls, v: LocalEmbeddings) -> list[list[float]]:
        return v.tolist()


class ProductSummary(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: UUID
    name: ProductName
    image: Image


class Product(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: UUID
    name: ProductName
    category: CategoryMap
    formats: Sequence[Format]
    images: Sequence[Image]


class StoredProduct(TimeStamped):
    # Allow ndarray while keeping strict round-trip via validators/serializers
    model_config = ConfigDict(arbitrary_types_allowed=True)
    id: UUID
    name: ProductName
    category: CategoryMap
    formats: Sequence[StoredFormat]
    images: Sequence[StoredImage]
    globalEmbedding: GlobalEmbedding

    # ---- NumPy GlobalEmbedding ser/de ----
    @field_validator("globalEmbedding", mode="before")
    @classmethod
    def _as_f32_1d(cls, v: Any) -> GlobalEmbedding:
        if v is None:
            return np.zeros((0,), dtype=np.float32)
        a = np.asarray(v, dtype=np.float32)
        if a.ndim != 1:
            raise ValueError("globalEmbedding must be 1D")
        return a

    @field_serializer("globalEmbedding")
    def _dump_global(cls, v: GlobalEmbedding) -> list[float]:
        return v.tolist()


# ──────────────────────────────────────────────────────────────────────────────
# Request Models
# ──────────────────────────────────────────────────────────────────────────────
class CreateProductRequest(BaseModel):
    model_config = ConfigDict(frozen=True)
    name: ProductName
    category: CategoryMap


class UpdateProductRequest(BaseModel):
    # All optional for PATCH
    model_config = ConfigDict(frozen=True)
    name: Optional[ProductName] = None  # null=clear
    category: Optional[Mapping[str, NonEmptyStr | None]] = None  # null=clear


class CreateFormatRequest(FormatBase): ...


class UpdateFormatRequest(BaseModel):
    model_config = ConfigDict(frozen=True)
    # All optional for PATCH
    aspect: Optional[NonEmptyStr] = None
    length: Optional[Dimension] = None  # null=clear
    width: Optional[Dimension] = None  # null=clear
    thickness: Optional[Dimension] = None  # null=clear


class CreateVendorRequest(VendorBase): ...


class UpdateVendorRequest(BaseModel):
    model_config = ConfigDict(frozen=True)
    # All optional for PATCH
    sku: Optional[NonEmptyStr] = None
    store: Optional[NonEmptyStr] = None
    name: Optional[NonEmptyStr] = None
    price: Optional[Currency] = None  # null=clear
    discontinued: Optional[bool] = None  # null=clear
    url: Optional[AnyUrl] = None  # null=clear


class ImageUploadRequest(BaseModel):
    model_config = ConfigDict(frozen=True)
    image: bytes
    mask: Optional[NonEmptyStr] = None
    hom: Optional[NonEmptyStr] = None


class ImageUpdateRequest(BaseModel):
    model_config = ConfigDict(frozen=True)
    reset: bool = False
    mask: Optional[NonEmptyStr] = None
    hom: Optional[NonEmptyStr] = None
