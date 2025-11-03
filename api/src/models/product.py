#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Mapping, Sequence, Optional
from uuid import UUID

import numpy as np
from numpy.typing import NDArray
from pydantic import BaseModel, AnyUrl

from .common import (
    CategoryMap,
    NonEmptyStr,
    TimeStamped,
)

# ──────────────────────────────────────────────────────────────────────────────
# Type Aliases (provider-level, API-agnostic)
# ──────────────────────────────────────────────────────────────────────────────
ImageMask = NDArray[np.bool_]
HomographyMatrix = NDArray[np.float64]  # 3x3 numeric matrix
LocalEmbeddings = NDArray[np.float32]  # per-image dense local vectors
GlobalEmbedding = NDArray[np.float32]  # per-product global vector


# ──────────────────────────────────────────────────────────────────────────────
# Core Shared Models
# ──────────────────────────────────────────────────────────────────────────────
class Dimension(BaseModel):
    value: int
    unit: NonEmptyStr


class Currency(BaseModel):
    value: int
    unit: NonEmptyStr


class ProductName(BaseModel):
    """Unified product name schema; all fields optional for create/patch/partial."""

    brand: Optional[NonEmptyStr] = None
    series: Optional[NonEmptyStr] = None
    model: Optional[NonEmptyStr] = None


# ──────────────────────────────────────────────────────────────────────────────
# Vendor / Format / Product
# ──────────────────────────────────────────────────────────────────────────────
class VendorBase(BaseModel):
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
    id: UUID
    url: AnyUrl


class StoredImage(TimeStamped):
    id: UUID
    localEmbeddings: Optional[LocalEmbeddings] = None


class ProductSummary(BaseModel):
    id: UUID
    name: ProductName
    image: Image


class Product(BaseModel):
    id: UUID
    name: ProductName
    category: CategoryMap
    formats: Sequence[Format]
    images: Sequence[Image]


class StoredProduct(TimeStamped):
    id: UUID
    name: ProductName
    category: CategoryMap
    formats: Sequence[StoredFormat]
    images: Sequence[StoredImage]
    globalEmbedding: Optional[GlobalEmbedding] = None


# ──────────────────────────────────────────────────────────────────────────────
# Request Models
# ──────────────────────────────────────────────────────────────────────────────
class CreateProductRequest(BaseModel):
    name: ProductName
    category: CategoryMap


class UpdateProductRequest(BaseModel):
    # All optional for PATCH
    name: Optional[ProductName] = None  # null=clear
    category: Optional[Mapping[str, NonEmptyStr | None]] = None  # null=clear


class CreateFormatRequest(FormatBase): ...


class UpdateFormatRequest(BaseModel):
    # All optional for PATCH
    aspect: Optional[NonEmptyStr] = None
    length: Optional[Dimension] = None  # null=clear
    width: Optional[Dimension] = None  # null=clear
    thickness: Optional[Dimension] = None  # null=clear


class CreateVendorRequest(VendorBase): ...


class UpdateVendorRequest(BaseModel):
    # All optional for PATCH
    sku: Optional[NonEmptyStr] = None
    store: Optional[NonEmptyStr] = None
    name: Optional[NonEmptyStr] = None
    price: Optional[Currency] = None  # null=clear
    discontinued: Optional[bool] = None  # null=clear
    url: Optional[AnyUrl] = None  # null=clear


class ImageUploadRequest(BaseModel):
    image: bytes
    mask: Optional[NonEmptyStr] = None
    hom: Optional[NonEmptyStr] = None


class ImageUpdateRequest(BaseModel):
    reset: bool = False
    mask: Optional[NonEmptyStr] = None
    hom: Optional[NonEmptyStr] = None
