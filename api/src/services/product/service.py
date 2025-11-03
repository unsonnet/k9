#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations
from datetime import datetime, timezone
from typing import NoReturn, TypeVar
from uuid import UUID, uuid4
import base64
import json
import struct

import numpy as np

from config import settings
from utils.http import (
    HttpError,
    Conflict,
    Created,
    Forbidden,
    InternalServerError,
    NoContent,
    NotFound,
    OK,
    TooManyRequests,
    Unauthorized,
    Gone,
)
from models.auth import AuthContext
from models.product import (
    CreateProductRequest,
    UpdateProductRequest,
    CreateFormatRequest,
    UpdateFormatRequest,
    CreateVendorRequest,
    UpdateVendorRequest,
    ImageUploadRequest,
    ImageUpdateRequest,
    ProductName,
    Product,
    Format,
    Vendor,
    Image,
    StoredProduct,
    StoredFormat,
    StoredVendor,
    StoredImage,
    HomographyMatrix,
    ImageMask,
)
from utils.errors import (
    DomainConflict,
    DomainExpiredToken,
    DomainInvariantViolation,
    DomainNotFound,
    DomainRateLimited,
    DomainUnauthorized,
    DomainUserDisabled,
    DomainForbidden,
)
from services.user.service import UserService
from .provider import ProductDBProvider, ImageDBProvider

T = TypeVar("T")


# ──────────────────────────────────────────────────────────────────────────────
# Product Service
# ──────────────────────────────────────────────────────────────────────────────
class ProductService:
    """Orchestrate product, format, vendor, and image operations via configured providers."""

    db: ProductDBProvider
    images: ImageDBProvider
    users: UserService

    def __init__(self) -> None:
        # For now, default to noop providers only. Concrete providers will be added later.
        from .provider import _NoopProductDBProvider, _NoopImageDBProvider

        _ = settings()  # kept for parity with other services; not used yet
        self.db = _NoopProductDBProvider()
        self.images = _NoopImageDBProvider()
        self.users = UserService()

    # ─────────── Helpers ───────────
    @staticmethod
    def _handle_error(e: Exception) -> NoReturn:
        """Map domain errors to HTTP responses."""
        m: dict[type[Exception], type[HttpError]] = {
            DomainNotFound: NotFound,
            DomainConflict: Conflict,
            DomainUnauthorized: Unauthorized,
            DomainForbidden: Forbidden,
            DomainUserDisabled: Forbidden,
            DomainExpiredToken: Gone,
            DomainRateLimited: TooManyRequests,
            DomainInvariantViolation: InternalServerError,
        }
        raise m.get(type(e), InternalServerError).from_exception(e)

    @staticmethod
    def _now() -> datetime:
        """Current UTC timestamp."""
        return datetime.now(timezone.utc)

    @staticmethod
    def _touch(obj: T, **x) -> T:
        """Apply update timestamp."""
        # Pydantic v2 model_copy works on our Stored* models.
        return obj.model_copy(update={**x, "updatedAt": datetime.now(timezone.utc)})  # type: ignore

    # Public mappers to API schemas
    @staticmethod
    def _public_vendor(v: StoredVendor) -> Vendor:
        """Sanitize vendor to public view."""
        return Vendor(
            id=v.id,
            sku=v.sku,
            store=v.store,
            name=v.name,
            price=v.price,
            discontinued=v.discontinued,
            url=v.url,
        )

    def _public_format(self, f: StoredFormat) -> Format:
        """Sanitize format to public view."""
        return Format(
            id=f.id,
            aspect=f.aspect,
            length=f.length,
            width=f.width,
            thickness=f.thickness,
            vendors=[self._public_vendor(v) for v in (f.vendors or [])],
        )

    def _public_image(self, pid: UUID, i: StoredImage) -> Image:
        """Sanitize image to public view, resolving URL via image provider."""
        return Image(
            id=i.id, url=self.images.get_url(pid=pid, iid=i.id, original=False)
        )

    def _public_product(self, p: StoredProduct) -> Product:
        """Sanitize product to public view."""
        return Product(
            id=p.id,
            name=p.name,
            category=p.category,
            formats=[self._public_format(f) for f in (p.formats or [])],
            images=[self._public_image(p.id, i) for i in (p.images or [])],
        )

    # ─────────── Noncontract Methods ───────────

    def _require_admin(self, ctx: AuthContext) -> None:
        """Enforce admin authorization using UserService semantics."""
        if not self.users.is_admin(ctx):
            raise DomainForbidden("Request denied.")

    def _parse_mask(self, mask: str | None) -> ImageMask | None:
        """
        Decode base64-encoded compact 2D boolean mask.
        """
        if mask is None:
            return None

        try:
            raw = base64.b64decode(mask, validate=True)
        except Exception as e:
            raise DomainInvariantViolation("Invalid base64 for mask.") from e

        if len(raw) < 8:
            raise DomainInvariantViolation("Mask too short to contain shape header.")

        # Parse header (big endian uint32)
        height, width = struct.unpack_from(">II", raw, 0)
        if height <= 0 or width <= 0:
            raise DomainInvariantViolation("Invalid mask shape.")

        nbits = height * width
        nbytes = (nbits + 7) // 8
        data = raw[8 : 8 + nbytes]
        if len(data) < nbytes:
            raise DomainInvariantViolation("Truncated mask payload.")

        # Convert to bits efficiently
        bits = np.unpackbits(np.frombuffer(data, dtype=np.uint8))
        mask_arr = bits[:nbits].reshape((height, width))
        return mask_arr.astype(bool)

    def _parse_homography(self, hom: str | None) -> HomographyMatrix | None:
        """
        Decode base64-encoded binary 3x3 homography matrix.
        """
        if hom is None:
            return None

        try:
            raw = base64.b64decode(hom, validate=True)
        except Exception as e:
            raise DomainInvariantViolation("Invalid base64 for homography.") from e

        # Accept only binary encodings
        for dtype in (
            np.dtype("<f4"),
            np.dtype(">f4"),
            np.dtype("<f8"),
            np.dtype(">f8"),
        ):
            nbytes = 9 * dtype.itemsize
            if len(raw) == nbytes:
                arr = np.frombuffer(raw, dtype=dtype, count=9)
                return arr.astype(np.float64).reshape((3, 3))

        raise DomainInvariantViolation(
            "Homography must be binary base64 of 9 float32/float64 values (row-major)."
        )

    # ─────────── Contract Methods ───────────
    # POST /product → 201 | 400 | 401 | 409 | 429 | 500
    def create_product(
        self, ctx: AuthContext, p: CreateProductRequest
    ) -> Created[Product]:
        """Create a new product."""
        try:
            created = self.db.post_product(name=p.name, category=p.category)
            return Created(self._public_product(created))
        except Exception as e:
            self._handle_error(e)

    # GET /product/{pid} → 200 | 401 | 404 | 429 | 500
    def get_product(self, ctx: AuthContext, pid: UUID) -> OK[Product]:
        """Retrieve product by id."""
        try:
            stored = self.db.get_product(pid=pid, embeddings=False)
            return OK(self._public_product(stored))
        except Exception as e:
            self._handle_error(e)

    # PATCH /product/{pid} → 200 | 400 | 401 | 404 | 429 | 500
    def update_product(
        self, ctx: AuthContext, pid: UUID, p: UpdateProductRequest
    ) -> OK[Product]:
        """Update a product by id."""
        try:
            prod = self.db.get_product(pid=pid, embeddings=False)

            # Name partial patch (brand/series/model may be nullable)
            if p.name is not None:
                patch = p.name.model_dump(exclude_unset=True)
                prod.name = ProductName(
                    brand=patch.get("brand", prod.name.brand),
                    series=patch.get("series", prod.name.series),
                    model=patch.get("model", prod.name.model),
                )

            # Category map merge; null removes the key
            if p.category is not None:
                cat = dict(prod.category or {})
                for k, v in p.category.items():
                    if v is None:
                        cat.pop(k, None)
                    else:
                        cat[k] = v
                prod.category = cat

            saved = self.db.put_product(product=self._touch(prod))
            return OK(self._public_product(saved))
        except Exception as e:
            self._handle_error(e)

    # DELETE /product/{pid} → 204 | 400 | 401 | 403 | 404 | 429 | 500
    def delete_product(self, ctx: AuthContext, pid: UUID) -> NoContent:
        """Delete a product by id. Requires admin."""
        try:
            self._require_admin(ctx)
            self.db.delete_product(pid=pid)
            return NoContent()
        except Exception as e:
            self._handle_error(e)

    # ─────────── Format ───────────
    # POST /product/{pid}/format → 201 | 400 | 401 | 404 | 409 | 429 | 500
    def create_format(
        self, ctx: AuthContext, pid: UUID, p: CreateFormatRequest
    ) -> Created[Format]:
        """Create a new format for a product."""
        try:
            prod = self.db.get_product(pid=pid, embeddings=False)
            fmt = StoredFormat(
                id=uuid4(),
                aspect=p.aspect,
                length=p.length,
                width=p.width,
                thickness=p.thickness,
                vendors=[],
                createdAt=self._now(),
            )
            updated = self._touch(prod, formats=[*(prod.formats or []), fmt])
            saved = self.db.put_product(product=updated)
            # Return the created format as stored (IDs may be used by client immediately)
            # Choose the one with fmt.id to avoid relying on order.
            created_fmt = next(f for f in saved.formats if f.id == fmt.id)
            return Created(self._public_format(created_fmt))
        except Exception as e:
            self._handle_error(e)

    # PATCH /product/{pid}/format/{fid} → 200 | 400 | 401 | 404 | 429 | 500
    def update_format(
        self, ctx: AuthContext, pid: UUID, fid: UUID, p: UpdateFormatRequest
    ) -> OK[Format]:
        """Update a product format."""
        try:
            prod = self.db.get_product(pid=pid, embeddings=False)
            fmt = next((f for f in (prod.formats or []) if f.id == fid), None)
            if not fmt:
                raise DomainNotFound("Format not found.")

            # Aspect and dimensions: replace provided values; allow explicit nulls per OpenAPI
            if p.aspect is not None:
                fmt.aspect = p.aspect
            if "length" in p.model_fields_set:
                fmt.length = p.length  # may be None
            if "width" in p.model_fields_set:
                fmt.width = p.width  # may be None
            if "thickness" in p.model_fields_set:
                fmt.thickness = p.thickness  # may be None

            fmt = self._touch(fmt)
            new_formats = [fmt if f.id == fid else f for f in (prod.formats or [])]
            saved = self.db.put_product(product=self._touch(prod, formats=new_formats))
            updated_fmt = next(f for f in saved.formats if f.id == fid)
            return OK(self._public_format(updated_fmt))
        except Exception as e:
            self._handle_error(e)

    # DELETE /product/{pid}/format/{fid} → 204 | 401 | 403 | 404 | 429 | 500
    def delete_format(self, ctx: AuthContext, pid: UUID, fid: UUID) -> NoContent:
        """Delete a product format. Requires admin."""
        try:
            self._require_admin(ctx)
            prod = self.db.get_product(pid=pid, embeddings=False)
            if not any(f.id == fid for f in (prod.formats or [])):
                raise DomainNotFound("Format not found.")
            new_formats = [f for f in prod.formats if f.id != fid]
            self.db.put_product(product=self._touch(prod, formats=new_formats))
            return NoContent()
        except Exception as e:
            self._handle_error(e)

    # ─────────── Vendor ───────────
    # POST /product/{pid}/format/{fid}/vendor → 201 | 400 | 401 | 404 | 409 | 429 | 500
    def create_vendor(
        self, ctx: AuthContext, pid: UUID, fid: UUID, p: CreateVendorRequest
    ) -> Created[Vendor]:
        """Create a vendor listing for a format."""
        try:
            prod = self.db.get_product(pid=pid, embeddings=False)
            fmt = next((f for f in (prod.formats or []) if f.id == fid), None)
            if not fmt:
                raise DomainNotFound("Format not found.")
            ven = StoredVendor(
                id=uuid4(),
                sku=p.sku,
                store=p.store,
                name=p.name,
                price=p.price,
                discontinued=p.discontinued,
                url=p.url,
                createdAt=self._now(),
            )
            fmt = self._touch(fmt, vendors=[*(fmt.vendors or []), ven])
            new_formats = [fmt if f.id == fid else f for f in (prod.formats or [])]
            saved = self.db.put_product(product=self._touch(prod, formats=new_formats))
            created_ven = next(
                v
                for f in saved.formats
                if f.id == fid
                for v in f.vendors
                if v.id == ven.id
            )
            return Created(self._public_vendor(created_ven))
        except Exception as e:
            self._handle_error(e)

    # PATCH /product/{pid}/format/{fid}/vendor/{vid} → 200 | 400 | 401 | 404 | 429 | 500
    def update_vendor(
        self, ctx: AuthContext, pid: UUID, fid: UUID, vid: UUID, p: UpdateVendorRequest
    ) -> OK[Vendor]:
        """Update a vendor listing."""
        try:
            prod = self.db.get_product(pid=pid, embeddings=False)
            fmt = next((f for f in (prod.formats or []) if f.id == fid), None)
            if not fmt:
                raise DomainNotFound("Format not found.")
            ven = next((v for v in (fmt.vendors or []) if v.id == vid), None)
            if not ven:
                raise DomainNotFound("Vendor not found.")

            # Replace provided fields; allow explicit nulls per OpenAPI (price/url/discontinued may be null)
            if p.sku is not None:
                ven.sku = p.sku
            if p.store is not None:
                ven.store = p.store
            if p.name is not None:
                ven.name = p.name
            if "price" in p.model_fields_set:
                ven.price = p.price
            if "discontinued" in p.model_fields_set:
                ven.discontinued = p.discontinued
            if "url" in p.model_fields_set:
                ven.url = p.url

            ven = self._touch(ven)
            new_vendors = [ven if v.id == vid else v for v in (fmt.vendors or [])]
            fmt = self._touch(fmt, vendors=new_vendors)
            new_formats = [fmt if f.id == fid else f for f in (prod.formats or [])]
            saved = self.db.put_product(product=self._touch(prod, formats=new_formats))
            updated_ven = next(
                v
                for f in saved.formats
                if f.id == fid
                for v in f.vendors
                if v.id == vid
            )
            return OK(self._public_vendor(updated_ven))
        except Exception as e:
            self._handle_error(e)

    # DELETE /product/{pid}/format/{fid}/vendor/{vid} → 204 | 401 | 403 | 404 | 429 | 500
    def delete_vendor(
        self, ctx: AuthContext, pid: UUID, fid: UUID, vid: UUID
    ) -> NoContent:
        """Delete a vendor listing. Requires admin."""
        try:
            self._require_admin(ctx)
            prod = self.db.get_product(pid=pid, embeddings=False)
            fmt = next((f for f in (prod.formats or []) if f.id == fid), None)
            if not fmt:
                raise DomainNotFound("Format not found.")
            if not any(v.id == vid for v in (fmt.vendors or [])):
                raise DomainNotFound("Vendor not found.")

            new_vendors = [v for v in fmt.vendors if v.id != vid]
            fmt = self._touch(fmt, vendors=new_vendors)
            new_formats = [fmt if f.id == fid else f for f in (prod.formats or [])]
            self.db.put_product(product=self._touch(prod, formats=new_formats))
            return NoContent()
        except Exception as e:
            self._handle_error(e)

    # ─────────── Image ───────────
    # POST /product/{pid}/image → 201 | 400 | 401 | 404 | 429 | 500
    def upload_image(
        self, ctx: AuthContext, pid: UUID, p: ImageUploadRequest
    ) -> Created[Image]:
        """Upload product image with mask and homography metadata."""
        try:
            prod = self.db.get_product(pid=pid, embeddings=False)

            # Store original image and compute embeddings/ids at provider level.
            iid, loc, glob = self.images.post_image(
                pid=pid,
                image=p.image,
                mask=self._parse_mask(p.mask),
                homography=self._parse_homography(p.hom),
            )

            # Append minimal stored image record; provider owns the actual blobs/embeddings.
            img = StoredImage(id=iid, localEmbeddings=loc, createdAt=self._now())
            new_images = [*(prod.images or []), img]
            saved = self.db.put_product(
                product=self._touch(prod, images=new_images, globalEmbedding=glob)
            )
            stored_img = next(i for i in saved.images if i.id == iid)
            return Created(self._public_image(pid, stored_img))
        except Exception as e:
            self._handle_error(e)

    # PATCH /product/{pid}/image/{iid} → 200 | 400 | 401 | 404 | 429 | 500
    def update_image(
        self, ctx: AuthContext, pid: UUID, iid: UUID, p: ImageUpdateRequest
    ) -> OK[Image]:
        """Update image metadata, recomputing provider artifacts as needed."""
        try:
            prod = self.db.get_product(pid=pid, embeddings=False)
            img = next((i for i in (prod.images or []) if i.id == iid), None)
            if not img:
                raise DomainNotFound("Image not found.")

            # Update provider metadata; provider may recompute embeddings/derivatives.
            loc, glob = self.images.put_image(
                pid=pid,
                iid=iid,
                mask=self._parse_mask(p.mask),
                homography=self._parse_homography(p.hom),
            )

            # Touch stored image record for bookkeeping.
            new_images = [
                self._touch(img, localEmbeddings=loc) if i.id == iid else i
                for i in (prod.images or [])
            ]
            saved = self.db.put_product(
                product=self._touch(prod, images=new_images, globalEmbedding=glob)
            )
            updated_img = next(i for i in saved.images if i.id == iid)
            return OK(self._public_image(pid, updated_img))
        except Exception as e:
            self._handle_error(e)

    # DELETE /product/{pid}/image/{iid} → 204 | 401 | 403 | 404 | 429 | 500
    def delete_image(self, ctx: AuthContext, pid: UUID, iid: UUID) -> NoContent:
        """Delete product image. Requires admin."""
        try:
            self._require_admin(ctx)
            prod = self.db.get_product(pid=pid, embeddings=False)
            if not any(i.id == iid for i in (prod.images or [])):
                raise DomainNotFound("Image not found.")

            # Remove provider artifacts first, then persist new product state.
            self.images.delete(pid=pid, iid=iid)
            new_images = [i for i in (prod.images or []) if i.id != iid]
            self.db.put_product(product=self._touch(prod, images=new_images))
            return NoContent()
        except Exception as e:
            self._handle_error(e)
