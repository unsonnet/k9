#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations
from datetime import datetime, timezone
from typing import NoReturn, TypeVar
from uuid import UUID, uuid4
import base64
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
from models.domain.auth import AuthContext
from models.api.product import (
    CreateProductRequest,
    UpdateProductRequest,
    CreateFormatRequest,
    UpdateFormatRequest,
    CreateVendorRequest,
    UpdateVendorRequest,
    UploadImageRequest,
    UpdateImageRequest,
)
from models.domain.product import (
    Name,
    Product,
    ProductSummary,
    ProductEntity,
    FormatInfo,
    FormatEntity,
    VendorInfo,
    VendorEntity,
    ImageInfo,
    ImageEntity,
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
from services.user import UserService
from providers.product import ProductDBProvider
from providers.image import ImageDBProvider

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
        from providers.product import DynamoProductDBProvider, _NoopProductDBProvider
        from providers.image import S3ImageDBProvider, _NoopImageDBProvider

        cfg = settings()

        # Full providers when deployed on AWS
        if cfg.platform == "aws":
            self.db = DynamoProductDBProvider()
            self.images = S3ImageDBProvider()

        # Local / dev fallback
        elif cfg.platform in {"dev", "local"}:
            self.db = _NoopProductDBProvider()
            self.images = _NoopImageDBProvider()

        # Fail clearly if neither condition applies
        else:
            raise InternalServerError("Failed to initialize product service.")

        # Sub-services initialized last
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
        """Return a *new* object with fields updated and updatedAt set (no in-place mutation)."""
        return obj.model_copy(update={**x, "updatedAt": datetime.now(timezone.utc)})  # type: ignore

    # Public mappers to API schemas
    @staticmethod
    def _public_vendor(v: VendorEntity) -> VendorInfo:
        """Convert stored vendor to public vendor."""
        return VendorInfo(
            id=v.id,
            sku=v.sku,
            store=v.store,
            name=v.name,
            price=v.price,
            discontinued=v.discontinued,
        )

    def _public_format(self, f: FormatEntity) -> FormatInfo:
        """Convert stored format to public format."""
        return FormatInfo(
            id=f.id,
            aspect=f.aspect,
            length=f.length,
            width=f.width,
            thickness=f.thickness,
            vendors=[self._public_vendor(v) for v in f.vendors],
        )

    def _public_image(self, pid: UUID, i: ImageEntity) -> ImageInfo:
        """Convert stored image to public image."""
        return ImageInfo(
            id=i.id, url=self.images.get_url(pid=pid, iid=i.id, transformed=False)
        )

    def _public_product(self, p: ProductEntity) -> Product:
        """Sanitize product to public view."""
        return Product(
            id=p.id,
            name=p.name,
            category=p.category,
            formats=[self._public_format(f) for f in p.formats],
            images=[self._public_image(p.id, i) for i in p.images],
        )

    # ─────────── Noncontract Methods ───────────

    def _require_admin(self, ctx: AuthContext) -> None:
        """Enforce admin authorization using UserService semantics."""
        if not self.users.is_admin(ctx):
            raise DomainForbidden("Request denied.")

    def _parse_mask(self, mask: bytes | None) -> ImageMask | None:
        """Decode compact binary 2D boolean mask from raw bytes.

        Layout:
        [0:8]   big-endian uint32 height, uint32 width
        [8:..]  packed bits row-major (MSB-first per byte)
        """
        if mask is None:
            return None
        raw = bytes(mask)

        if len(raw) < 8:
            raise DomainInvariantViolation("mask header truncated")
        height, width = struct.unpack_from(">II", raw, 0)
        if height <= 0 or width <= 0:
            raise DomainInvariantViolation("invalid mask shape")

        nbits = height * width
        nbytes = (nbits + 7) // 8
        payload = raw[8 : 8 + nbytes]
        if len(payload) < nbytes:
            raise DomainInvariantViolation("mask payload truncated")

        bits = np.unpackbits(np.frombuffer(payload, dtype=np.uint8))
        return bits[:nbits].reshape((height, width)).astype(bool)

    def _parse_homography(self, hom: bytes | None) -> HomographyMatrix | None:
        """Decode 3x3 homography matrix from raw bytes (row-major floats)."""
        if hom is None:
            return None
        raw = bytes(hom)

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
            "hom must be 9 float32/float64 values (row-major)"
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
            stored = self.db.get_product(pid=pid)
            return OK(self._public_product(stored))
        except Exception as e:
            self._handle_error(e)

    # PATCH /product/{pid} → 200 | 400 | 401 | 404 | 429 | 500
    def update_product(
        self, ctx: AuthContext, pid: UUID, p: UpdateProductRequest
    ) -> OK[Product]:
        """Update a product by id."""
        try:
            prod = self.db.get_product(pid=pid)

            updates: dict = {}

            # Name partial patch (brand/series/model may be nullable)
            if p.name is not None:
                patch = p.name.model_dump(exclude_unset=True)
                updates["name"] = Name(
                    brand=patch.get("brand", prod.name.brand),
                    series=patch.get("series", prod.name.series),
                    model=patch.get("model", prod.name.model),
                )

            # Category map merge; null removes the key
            if p.category is not None:
                cat = dict(prod.category)
                for k, v in p.category.items():
                    if v is None:
                        cat.pop(k, None)
                    else:
                        cat[k] = v
                updates["category"] = cat

            updated_prod = (
                self._touch(prod, **updates) if updates else self._touch(prod)
            )
            saved = self.db.put_product(product=updated_prod)
            return OK(self._public_product(saved))
        except Exception as e:
            self._handle_error(e)

    # DELETE /product/{pid} → 204 | 400 | 401 | 403 | 404 | 429 | 500
    def delete_product(self, ctx: AuthContext, pid: UUID) -> NoContent:
        """Delete a product by id. Requires admin."""
        try:
            self._require_admin(ctx)
            prod = self.db.get_product(pid=pid)
            self.db.delete_product(pid=pid)
            self.images.delete_images(pid=pid, iids=[i.id for i in prod.images])
            return NoContent()
        except Exception as e:
            self._handle_error(e)

    # ─────────── Format ───────────
    # POST /product/{pid}/format → 201 | 400 | 401 | 404 | 409 | 429 | 500
    def create_format(
        self, ctx: AuthContext, pid: UUID, p: CreateFormatRequest
    ) -> Created[FormatInfo]:
        """Create a new format for a product."""
        try:
            prod = self.db.get_product(pid=pid)
            fmt = FormatEntity(
                id=uuid4(),
                aspect=p.aspect,
                length=p.length,
                width=p.width,
                thickness=p.thickness,
                vendors=[],
                created_at=self._now(),
            )
            updated = self._touch(prod, formats=[*prod.formats, fmt])
            saved = self.db.put_product(product=updated)
            created_fmt = next(f for f in saved.formats if f.id == fmt.id)
            return Created(self._public_format(created_fmt))
        except Exception as e:
            self._handle_error(e)

    # PATCH /product/{pid}/format/{fid} → 200 | 400 | 401 | 404 | 429 | 500
    def update_format(
        self, ctx: AuthContext, pid: UUID, fid: UUID, p: UpdateFormatRequest
    ) -> OK[FormatInfo]:
        """Update a product format (immutable models → copy on write)."""
        try:
            prod = self.db.get_product(pid=pid)
            current = next((f for f in prod.formats if f.id == fid), None)
            if not current:
                raise DomainNotFound("Format not found.")

            upd: dict = {}
            if p.aspect is not None:
                upd["aspect"] = p.aspect
            if "length" in p.model_fields_set:
                upd["length"] = p.length
            if "width" in p.model_fields_set:
                upd["width"] = p.width
            if "thickness" in p.model_fields_set:
                upd["thickness"] = p.thickness

            updated_fmt = self._touch(current, **upd) if upd else self._touch(current)
            new_formats = [updated_fmt if f.id == fid else f for f in prod.formats]
            saved = self.db.put_product(product=self._touch(prod, formats=new_formats))
            final_fmt = next(f for f in saved.formats if f.id == fid)
            return OK(self._public_format(final_fmt))
        except Exception as e:
            self._handle_error(e)

    # DELETE /product/{pid}/format/{fid} → 204 | 401 | 403 | 404 | 429 | 500
    def delete_format(self, ctx: AuthContext, pid: UUID, fid: UUID) -> NoContent:
        """Delete a product format. Requires admin."""
        try:
            self._require_admin(ctx)
            prod = self.db.get_product(pid=pid)
            if not any(f.id == fid for f in prod.formats):
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
    ) -> Created[VendorInfo]:
        """Create a vendor listing for a format."""
        try:
            prod = self.db.get_product(pid=pid)
            fmt = next((f for f in prod.formats if f.id == fid), None)
            if not fmt:
                raise DomainNotFound("Format not found.")
            ven = VendorEntity(
                id=uuid4(),
                sku=p.sku,
                store=p.store,
                name=p.name,
                price=p.price,
                discontinued=p.discontinued,
                created_at=self._now(),
            )
            fmt_updated = self._touch(fmt, vendors=[*fmt.vendors, ven])
            new_formats = [fmt_updated if f.id == fid else f for f in prod.formats]
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
    ) -> OK[VendorInfo]:
        """Update a vendor listing (immutable models → copy on write)."""
        try:
            prod = self.db.get_product(pid=pid)
            fmt = next((f for f in prod.formats if f.id == fid), None)
            if not fmt:
                raise DomainNotFound("Format not found.")
            current = next((v for v in fmt.vendors if v.id == vid), None)
            if not current:
                raise DomainNotFound("Vendor not found.")

            upd: dict = {}
            if p.sku is not None:
                upd["sku"] = p.sku
            if p.store is not None:
                upd["store"] = p.store
            if p.name is not None:
                upd["name"] = p.name
            if "price" in p.model_fields_set:
                upd["price"] = p.price
            if "discontinued" in p.model_fields_set:
                upd["discontinued"] = p.discontinued
            if "url" in p.model_fields_set:
                upd["url"] = p.url

            updated_vendor = (
                self._touch(current, **upd) if upd else self._touch(current)
            )
            new_vendors = [updated_vendor if v.id == vid else v for v in fmt.vendors]
            fmt_updated = self._touch(fmt, vendors=new_vendors)
            new_formats = [fmt_updated if f.id == fid else f for f in prod.formats]
            saved = self.db.put_product(product=self._touch(prod, formats=new_formats))
            final_vendor = next(
                v
                for f in saved.formats
                if f.id == fid
                for v in f.vendors
                if v.id == vid
            )
            return OK(self._public_vendor(final_vendor))
        except Exception as e:
            self._handle_error(e)

    # DELETE /product/{pid}/format/{fid}/vendor/{vid} → 204 | 401 | 403 | 404 | 429 | 500
    def delete_vendor(
        self, ctx: AuthContext, pid: UUID, fid: UUID, vid: UUID
    ) -> NoContent:
        """Delete a vendor listing. Requires admin."""
        try:
            self._require_admin(ctx)
            prod = self.db.get_product(pid=pid)
            fmt = next((f for f in prod.formats if f.id == fid), None)
            if not fmt:
                raise DomainNotFound("Format not found.")
            if not any(v.id == vid for v in fmt.vendors):
                raise DomainNotFound("Vendor not found.")

            new_vendors = [v for v in fmt.vendors if v.id != vid]
            fmt_updated = self._touch(fmt, vendors=new_vendors)
            new_formats = [fmt_updated if f.id == fid else f for f in prod.formats]
            self.db.put_product(product=self._touch(prod, formats=new_formats))
            return NoContent()
        except Exception as e:
            self._handle_error(e)

    # ─────────── Image ───────────
    # POST /product/{pid}/image → 201 | 400 | 401 | 404 | 429 | 500
    def upload_image(
        self, ctx: AuthContext, pid: UUID, p: UploadImageRequest
    ) -> Created[ImageInfo]:
        """Upload product image with mask and homography metadata."""
        try:
            prod = self.db.get_product(pid=pid)

            # Store original image and compute embeddings/ids at provider level.
            iid, loc, glob = self.images.post_image(
                pid=pid,
                image=p.image,
                mask=self._parse_mask(p.mask),
                homography=self._parse_homography(p.homography),
            )

            # Append minimal stored image record; provider owns the actual blobs/embeddings.
            img = ImageEntity(id=iid, local_embeddings=loc, created_at=self._now())
            new_images = [*prod.images, img]
            saved = self.db.put_product(
                product=self._touch(prod, images=new_images, globalEmbedding=glob)
            )
            stored_img = next(i for i in saved.images if i.id == iid)
            return Created(self._public_image(pid, stored_img))
        except Exception as e:
            self._handle_error(e)

    # PATCH /product/{pid}/image/{iid} → 200 | 400 | 401 | 404 | 429 | 500
    def update_image(
        self, ctx: AuthContext, pid: UUID, iid: UUID, p: UpdateImageRequest
    ) -> OK[ImageInfo]:
        """Update image metadata, recomputing provider artifacts as needed."""
        try:
            prod = self.db.get_product(pid=pid)
            img = next((i for i in prod.images if i.id == iid), None)
            if not img:
                raise DomainNotFound("Image not found.")

            # Update provider metadata; provider may recompute embeddings/derivatives.
            loc, glob = self.images.put_image(
                pid=pid,
                iid=iid,
                reset=p.reset,
                mask=self._parse_mask(p.mask),
                homography=self._parse_homography(p.homography),
            )

            # Touch stored image record for bookkeeping (copy on write).
            new_images = [
                self._touch(img, local_embeddings=loc) if i.id == iid else i
                for i in prod.images
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
            prod = self.db.get_product(pid=pid)
            if not any(i.id == iid for i in prod.images):
                raise DomainNotFound("Image not found.")

            # Remove provider artifacts first, then persist new product state.
            self.images.delete_images(pid=pid, iids=[iid])
            new_images = [i for i in prod.images if i.id != iid]
            self.db.put_product(product=self._touch(prod, images=new_images))
            return NoContent()
        except Exception as e:
            self._handle_error(e)
