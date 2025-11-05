#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Product API models - Request/Response DTOs for product endpoints."""

from __future__ import annotations

from typing import Mapping, Optional, Sequence
from uuid import UUID
from pydantic import AnyUrl

from ..shared.base import ApiModel
from ..shared.types import CategoryMap, NonEmptyStr
from ..shared.values import Currency, Dimension, Name

# ──────────────────────────────────────────────────────────────────────────────
# Request Models
# ──────────────────────────────────────────────────────────────────────────────


class CreateProductRequest(ApiModel):
    """Create new product request."""

    name: Name
    category: CategoryMap


class UpdateProductRequest(ApiModel):
    """Update product request - all fields optional for PATCH."""

    name: Optional[Name] = None
    category: Optional[Mapping[str, NonEmptyStr | None]] = None


class CreateFormatRequest(ApiModel):
    """Create product format request."""

    aspect: NonEmptyStr
    length: Optional[Dimension] = None
    width: Optional[Dimension] = None
    thickness: Optional[Dimension] = None


class UpdateFormatRequest(ApiModel):
    """Update format request - all fields optional for PATCH."""

    aspect: Optional[NonEmptyStr] = None
    length: Optional[Dimension] = None
    width: Optional[Dimension] = None
    thickness: Optional[Dimension] = None


class CreateVendorRequest(ApiModel):
    """Create vendor request."""

    sku: NonEmptyStr
    store: NonEmptyStr
    name: NonEmptyStr
    price: Optional[Currency] = None
    discontinued: Optional[bool] = None
    url: Optional[AnyUrl] = None


class UpdateVendorRequest(ApiModel):
    """Update vendor request - all fields optional for PATCH."""

    sku: Optional[NonEmptyStr] = None
    store: Optional[NonEmptyStr] = None
    name: Optional[NonEmptyStr] = None
    price: Optional[Currency] = None
    discontinued: Optional[bool] = None
    url: Optional[AnyUrl] = None


class UploadImageRequest(ApiModel):
    """Upload product image request."""

    image: bytes
    mask: Optional[bytes] = None
    homography: Optional[bytes] = None


class UpdateImageRequest(ApiModel):
    """Update product image request."""

    reset: bool = False
    mask: Optional[bytes] = None
    homography: Optional[bytes] = None


# ──────────────────────────────────────────────────────────────────────────────
# Response Models
# ──────────────────────────────────────────────────────────────────────────────


class ImageResponse(ApiModel):
    """Product image information for API responses."""

    id: UUID
    url: AnyUrl


class VendorResponse(ApiModel):
    """Vendor information for API responses."""

    id: UUID
    sku: NonEmptyStr
    store: NonEmptyStr
    name: NonEmptyStr
    price: Optional[Currency] = None
    discontinued: Optional[bool] = None
    url: Optional[AnyUrl] = None


class FormatResponse(ApiModel):
    """Format information for API responses."""

    id: UUID
    aspect: NonEmptyStr
    length: Optional[Dimension] = None
    width: Optional[Dimension] = None
    thickness: Optional[Dimension] = None
    vendors: Sequence[VendorResponse] = ()


class ProductSummaryResponse(ApiModel):
    """Product summary for listings."""

    id: UUID
    name: Name
    image: ImageResponse


class ProductResponse(ApiModel):
    """Complete product information for API responses."""

    id: UUID
    name: Name
    category: CategoryMap
    formats: Sequence[FormatResponse]
    images: Sequence[ImageResponse]
