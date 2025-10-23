#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations
from datetime import datetime, timezone
from typing import Sequence, TypeVar, NoReturn
from uuid import UUID, uuid4
from pydantic import BaseModel

# Typed HTTP responses/errors
from utils.http import (
    OK,
    Created,
    NoContent,
    Unauthorized,
    Forbidden,
    NotFound,
    InternalServerError,
)

M = TypeVar("M", bound=BaseModel)

# ──────────────────────────────────────────────────────────────────────────────
from models.common import AuthContext
from models.product import (
    Name,
    Vendor,
    Format,
    Image,
    Product,
    StoredVendor,
    StoredFormat,
    StoredImage,
    StoredProduct,
    CreateProductRequest,
    UpdateProductRequest,
    CreateFormatRequest,
    UpdateFormatRequest,
    CreateVendorRequest,
    UpdateVendorRequest,
    ImageUploadRequest,
    ImageUpdateRequest,
)


# ──────────────────────────────────────────────────────────────────────────────
# Domain Errors
from ..errors import (
    DomainUnauthorized,
    DomainForbidden,
    DomainNotFound,
    DomainInvariantViolation,
)

from .provider import (
    ProductDBProvider,
    ImageDBProvider,
    EmbeddingIndexProvider,
    NoopEmbeddingIndexProvider,
)


# ──────────────────────────────────────────────────────────────────────────────
# Product Service
# ──────────────────────────────────────────────────────────────────────────────
class ProductService:
    """
    API-facing orchestrator for product, format, vendor, and image operations.
    Maps domain-layer exceptions to HTTP responses and enforces business semantics.
    Provider owns IDs for products and images; service owns IDs for formats and vendors.
    """

    def __init__(
        self,
        db: ProductDBProvider,
        images: ImageDBProvider,
        embed_index: EmbeddingIndexProvider | None = None,
    ):
        self.db = db
        self.images = images
        self.embed = embed_index or NoopEmbeddingIndexProvider()

    # ──────────────────────────── Helpers ────────────────────────────
    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _touch(obj: M, **updates) -> M:
        return obj.model_copy(
            update={**updates, "updatedAt": datetime.now(timezone.utc)}
        )

    def _handle_error(self, e: Exception, msg: str = "Internal error") -> NoReturn:
        mapping = {
            DomainUnauthorized: lambda: Unauthorized("Not authorized."),
            DomainForbidden: lambda: Forbidden("Forbidden."),
            DomainNotFound: lambda: NotFound(msg),
            DomainInvariantViolation: lambda: InternalServerError(str(e)),
        }
        raise mapping.get(type(e), lambda: InternalServerError(str(e)))()

    # ──────────────────────────── Converters ────────────────────────────
    def _public_vendor(self, v: StoredVendor) -> Vendor:
        return Vendor(**v.model_dump())

    def _public_format(self, f: StoredFormat) -> Format:
        return Format(
            **f.model_dump(exclude={"vendors"}),
            vendors=[self._public_vendor(v) for v in f.vendors],
        )

    def _public_image(self, ctx: AuthContext, pid: UUID, i: StoredImage) -> Image:
        return Image(
            id=i.id, url=self.images.get_url(ctx, pid=pid, iid=i.id, kind="transformed")
        )

    def _public_product(self, ctx: AuthContext, p: StoredProduct) -> Product:
        return Product(
            id=p.id,
            name=p.name,
            category=p.category,
            formats=[self._public_format(f) for f in p.formats],
            images=[self._public_image(ctx, p.id, i) for i in p.images],
        )

    # ──────────────────────────── Product ────────────────────────────
    # POST /product → 201 | 400 | 401 | 403 | 500
    def create_product(
        self, ctx: AuthContext, payload: CreateProductRequest
    ) -> Created[Product]:
        try:
            stored = self.db.post_product(
                ctx,
                name=payload.name,
                category=payload.category,
            )
            return Created(self._public_product(ctx, stored))
        except Exception as e:
            self._handle_error(e, "Failed to create product.")

    # GET /product/{pid} → 200 | 401 | 403 | 404 | 500
    def get_product(self, ctx: AuthContext, pid: UUID) -> OK[Product]:
        try:
            return OK(self._public_product(ctx, self.db.get_product(ctx, pid=pid)))
        except Exception as e:
            self._handle_error(e, "Product not found.")

    # PATCH /product/{pid} → 200 | 400 | 401 | 403 | 404 | 500
    def update_product(
        self, ctx: AuthContext, pid: UUID, payload: UpdateProductRequest
    ) -> OK[Product]:
        try:
            prod = self.db.get_product(ctx, pid=pid)
            if payload.name is not None:
                patch = payload.name.model_dump(exclude_unset=True)
                prod.name = Name(
                    brand=patch.get("brand", prod.name.brand),
                    series=patch.get("series", prod.name.series),
                    model=patch.get("model", prod.name.model),
                )
            if payload.category is not None:
                new_cat = dict(prod.category)
                for k, v in payload.category.items():
                    if v is None:
                        new_cat.pop(k, None)
                    else:
                        new_cat[k] = v
                prod.category = new_cat
            updated = self._touch(prod)
            stored = self.db.put_product(ctx, product=updated)
            return OK(self._public_product(ctx, stored))
        except Exception as e:
            self._handle_error(e, "Failed to update product.")

    # DELETE /product/{pid} → 204 | 401 | 403 | 404 | 500
    def delete_product(self, ctx: AuthContext, pid: UUID) -> NoContent:
        try:
            self.db.delete_product(ctx, pid=pid)
            return NoContent()
        except Exception as e:
            self._handle_error(e, "Failed to delete product.")

    # ──────────────────────────── Format ────────────────────────────
    # POST /product/{pid}/format → 201 | 400 | 401 | 404 | 500
    def create_format(
        self, ctx: AuthContext, pid: UUID, payload: CreateFormatRequest
    ) -> Created[Format]:
        try:
            prod = self.db.get_product(ctx, pid=pid)
            fmt = StoredFormat(
                id=uuid4(),
                aspect=payload.aspect,
                length=payload.length,
                width=payload.width,
                thickness=payload.thickness,
                vendors=[],
                createdAt=self._now(),
                updatedAt=None,
            )
            updated = self._touch(prod, formats=[*prod.formats, fmt])
            self.db.put_product(ctx, product=updated)
            return Created(self._public_format(fmt))
        except Exception as e:
            self._handle_error(e, "Failed to create format.")

    # PATCH /product/{pid}/format/{fid} → 200 | 400 | 401 | 403 | 404 | 500
    def update_format(
        self, ctx: AuthContext, pid: UUID, fid: UUID, payload: UpdateFormatRequest
    ) -> OK[Format]:
        try:
            prod = self.db.get_product(ctx, pid=pid)
            fmt = next((f for f in prod.formats if f.id == fid), None)
            if not fmt:
                raise DomainNotFound()
            patch = payload.model_dump(exclude_unset=True)
            fmt = self._touch(fmt, **patch)
            updated_formats = [fmt if f.id == fid else f for f in prod.formats]
            updated = self._touch(prod, formats=updated_formats)
            self.db.put_product(ctx, product=updated)
            return OK(self._public_format(fmt))
        except Exception as e:
            self._handle_error(e, "Failed to update format.")

    # DELETE /product/{pid}/format/{fid} → 204 | 401 | 403 | 404 | 500
    def delete_format(self, ctx: AuthContext, pid: UUID, fid: UUID) -> NoContent:
        try:
            prod = self.db.get_product(ctx, pid=pid)
            if not any(f.id == fid for f in prod.formats):
                raise DomainNotFound()
            updated = self._touch(
                prod, formats=[f for f in prod.formats if f.id != fid]
            )
            self.db.put_product(ctx, product=updated)
            return NoContent()
        except Exception as e:
            self._handle_error(e, "Failed to delete format.")

    # ──────────────────────────── Vendor ────────────────────────────
    # POST /product/{pid}/format/{fid}/vendor → 201 | 400 | 401 | 404 | 500
    def create_vendor(
        self, ctx: AuthContext, pid: UUID, fid: UUID, payload: CreateVendorRequest
    ) -> Created[Vendor]:
        try:
            prod = self.db.get_product(ctx, pid=pid)
            fmt = next((f for f in prod.formats if f.id == fid), None)
            if not fmt:
                raise DomainNotFound()
            vendor = StoredVendor(
                id=uuid4(),
                sku=payload.sku,
                store=payload.store,
                name=payload.name,
                price=payload.price,
                discontinued=payload.discontinued,
                url=payload.url,
                createdAt=self._now(),
                updatedAt=None,
            )
            updated_fmt = self._touch(fmt, vendors=[*fmt.vendors, vendor])
            updated = self._touch(
                prod, formats=[updated_fmt if f.id == fid else f for f in prod.formats]
            )
            self.db.put_product(ctx, product=updated)
            return Created(self._public_vendor(vendor))
        except Exception as e:
            self._handle_error(e, "Failed to create vendor.")

    # PATCH /product/{pid}/format/{fid}/vendor/{vid} → 200 | 400 | 401 | 403 | 404 | 500
    def update_vendor(
        self,
        ctx: AuthContext,
        pid: UUID,
        fid: UUID,
        vid: UUID,
        payload: UpdateVendorRequest,
    ) -> OK[Vendor]:
        try:
            prod = self.db.get_product(ctx, pid=pid)
            fmt = next((f for f in prod.formats if f.id == fid), None)
            if not fmt:
                raise DomainNotFound()
            vendor = next((v for v in fmt.vendors if v.id == vid), None)
            if not vendor:
                raise DomainNotFound()
            patch = payload.model_dump(exclude_unset=True)
            vendor = self._touch(vendor, **patch)
            new_vendors = [vendor if v.id == vid else v for v in fmt.vendors]
            updated_fmt = self._touch(fmt, vendors=new_vendors)
            new_formats = [updated_fmt if f.id == fid else f for f in prod.formats]
            updated = self._touch(prod, formats=new_formats)
            self.db.put_product(ctx, product=updated)
            return OK(self._public_vendor(vendor))
        except Exception as e:
            self._handle_error(e, "Failed to update vendor.")

    # DELETE /product/{pid}/format/{fid}/vendor/{vid} → 204 | 401 | 403 | 404 | 500
    def delete_vendor(
        self, ctx: AuthContext, pid: UUID, fid: UUID, vid: UUID
    ) -> NoContent:
        try:
            prod = self.db.get_product(ctx, pid=pid)
            fmt = next((f for f in prod.formats if f.id == fid), None)
            if not fmt or not any(v.id == vid for v in fmt.vendors):
                raise DomainNotFound()
            updated_fmt = self._touch(
                fmt, vendors=[v for v in fmt.vendors if v.id != vid]
            )
            updated = self._touch(
                prod, formats=[updated_fmt if f.id == fid else f for f in prod.formats]
            )
            self.db.put_product(ctx, product=updated)
            return NoContent()
        except Exception as e:
            self._handle_error(e, "Failed to delete vendor.")

    # ──────────────────────────── Image ────────────────────────────
    # POST /product/{pid}/image → 201 | 400 | 401 | 403 | 404 | 500
    def upload_image(
        self, ctx: AuthContext, pid: UUID, payload: ImageUploadRequest
    ) -> Created[Image]:
        try:
            prod = self.db.get_product(ctx, pid=pid)
            transformed = self._transform_image(
                payload.image_bytes, payload.mask, payload.hom
            )
            meta = {"mask": payload.mask, "hom": payload.hom}
            iid = self.images.post_image(
                ctx,
                pid=pid,
                original_bytes=payload.image_bytes,
                transformed_bytes=transformed,
                metadata=meta,
            )
            local_vecs = self._compute_local_embeddings(transformed)
            stored_img = StoredImage(
                id=iid, createdAt=self._now(), localEmbeddings=local_vecs
            )
            all_local = [v for i in prod.images for v in (i.localEmbeddings or [])] + (
                local_vecs or []
            )
            global_vec = self._aggregate_global_embedding(all_local)
            updated = self._touch(
                prod, images=[*prod.images, stored_img], globalEmbedding=global_vec
            )
            self.db.put_product(ctx, product=updated)
            try:
                if global_vec:
                    self.embed.upsert_product_embedding(ctx, pid=pid, vector=global_vec)
                if local_vecs:
                    self.embed.upsert_image_local_embeddings(
                        ctx, pid=pid, iid=iid, vectors=local_vecs
                    )
            except Exception:
                pass
            return Created(self._public_image(ctx, pid, stored_img))
        except Exception as e:
            self._handle_error(e, "Failed to upload image.")

    # PATCH /product/{pid}/image/{iid} → 200 | 400 | 401 | 403 | 404 | 500
    def update_image(
        self, ctx: AuthContext, pid: UUID, iid: UUID, payload: ImageUpdateRequest
    ) -> OK[Image]:
        try:
            prod = self.db.get_product(ctx, pid=pid)
            img = next((i for i in prod.images if i.id == iid), None)
            if not img:
                raise DomainNotFound()
            patch = payload.model_dump(exclude_unset=True)
            if patch:
                self.images.put_image_metadata(ctx, pid=pid, iid=iid, metadata=patch)
            updated_img = self._touch(img)
            new_imgs = [updated_img if i.id == iid else i for i in prod.images]
            updated = self._touch(prod, images=new_imgs)
            self.db.put_product(ctx, product=updated)
            return OK(self._public_image(ctx, pid, updated_img))
        except Exception as e:
            self._handle_error(e, "Failed to update image.")

    # DELETE /product/{pid}/image/{iid} → 204 | 401 | 403 | 404 | 500
    def delete_image(self, ctx: AuthContext, pid: UUID, iid: UUID) -> NoContent:
        try:
            prod = self.db.get_product(ctx, pid=pid)
            if not any(i.id == iid for i in prod.images):
                raise DomainNotFound()
            self.images.delete(ctx, pid=pid, iid=iid)
            new_imgs = [i for i in prod.images if i.id != iid]
            all_local = [v for i in new_imgs for v in (i.localEmbeddings or [])]
            global_vec = self._aggregate_global_embedding(all_local)
            updated = self._touch(prod, images=new_imgs, globalEmbedding=global_vec)
            self.db.put_product(ctx, product=updated)
            try:
                self.embed.delete_image_local_embeddings(ctx, pid=pid, iid=iid)
                if global_vec:
                    self.embed.upsert_product_embedding(ctx, pid=pid, vector=global_vec)
                else:
                    self.embed.delete_product_embedding(ctx, pid=pid)
            except Exception:
                pass
            return NoContent()
        except Exception as e:
            self._handle_error(e, "Failed to delete image.")

    # ──────────────────────────── Embedding / Transform ────────────────────────────
    @staticmethod
    def _transform_image(original: bytes, mask: str, hom: str) -> bytes:
        """Placeholder: return original bytes; TODO apply mask/hom transformation."""
        return original

    @staticmethod
    def _compute_local_embeddings(_: bytes) -> list[list[float]] | None:
        """Placeholder: returns None."""
        return None

    @staticmethod
    def _aggregate_global_embedding(
        vectors: Sequence[Sequence[float]],
    ) -> list[float] | None:
        """Placeholder: Compute arithmetic mean of local embeddings."""
        if not vectors or not vectors[0]:
            return None
        dim = len(vectors[0])
        acc = [sum(col) / len(vectors) for col in zip(*vectors)]
        return acc if len(acc) == dim else None
