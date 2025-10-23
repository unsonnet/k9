#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Mapping, Sequence
from uuid import UUID

from pydantic import BaseModel, AnyUrl

from .common import (
    CategoryMap,
    NonEmptyStr,
    TimeStamped,
)


# ──────────────────────────────────────────────────────────────────────────────
# Core Models
# ──────────────────────────────────────────────────────────────────────────────
class Dimension(BaseModel):
    value: int
    unit: NonEmptyStr


class Currency(BaseModel):
    value: int
    unit: NonEmptyStr


class Name(BaseModel):
    brand: NonEmptyStr | None = None
    series: NonEmptyStr | None = None
    model: NonEmptyStr | None = None


# Partial name for PATCH semantics (omit=ignore, null=clear)
class NamePartial(BaseModel):
    brand: NonEmptyStr | None = None
    series: NonEmptyStr | None = None
    model: NonEmptyStr | None = None


# ──────────────────────────────────────────────────────────────────────────────
# Vendor / Format / Product
# ──────────────────────────────────────────────────────────────────────────────
class VendorBase(BaseModel):
    sku: NonEmptyStr
    store: NonEmptyStr
    name: NonEmptyStr
    price: Currency | None = None
    discontinued: bool | None = None
    url: AnyUrl | None = None


class Vendor(VendorBase):
    id: UUID


class StoredVendor(VendorBase, TimeStamped):
    id: UUID


class FormatBase(BaseModel):
    aspect: NonEmptyStr
    length: Dimension | None = None
    width: Dimension | None = None
    thickness: Dimension | None = None


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
    localEmbeddings: Sequence[Sequence[float]] | None = None


class ProductSummary(BaseModel):
    id: UUID
    name: Name
    image: Image


class Product(BaseModel):
    id: UUID
    name: Name
    category: CategoryMap
    formats: Sequence[Format]
    images: Sequence[Image]


class StoredProduct(TimeStamped):
    id: UUID
    name: Name
    category: CategoryMap
    formats: Sequence[StoredFormat]
    images: Sequence[StoredImage]
    globalEmbedding: Sequence[float] | None = None


# ──────────────────────────────────────────────────────────────────────────────
# Request Models
# ──────────────────────────────────────────────────────────────────────────────
class CreateProductRequest(BaseModel):
    name: Name
    category: CategoryMap


class UpdateProductRequest(BaseModel):
    name: NamePartial | None = None
    category: Mapping[str, NonEmptyStr | None] | None = None


class CreateFormatRequest(FormatBase): ...


class UpdateFormatRequest(BaseModel):
    # All optional for PATCH; null clears dimensions
    aspect: NonEmptyStr | None = None
    length: Dimension | None = None
    width: Dimension | None = None
    thickness: Dimension | None = None


class CreateVendorRequest(VendorBase): ...


class UpdateVendorRequest(BaseModel):
    # All optional; null clears value if applicable
    sku: NonEmptyStr | None = None
    store: NonEmptyStr | None = None
    name: NonEmptyStr | None = None
    price: Currency | None = None
    discontinued: bool | None = None
    url: AnyUrl | None = None


class ImageUploadRequest(BaseModel):
    image_bytes: bytes
    mask: NonEmptyStr
    hom: NonEmptyStr


class ImageUpdateRequest(BaseModel):
    mask: NonEmptyStr | None = None
    hom: NonEmptyStr | None = None
