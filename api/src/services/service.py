from __future__ import annotations

import base64
import io
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

try:
    from PIL import Image as PILImage  # type: ignore
except Exception:  # noqa: BLE001
    PILImage = None  # type: ignore

from config import settings
from models.api import (
    CreateFormatRequest,
    CreateProductRequest,
    CreateVendorRequest,
    PasswordUpdateRequest,
    RefreshRequest,
    ResetRequest,
    SearchRequest,
    TokenResponse,
    UpdateFormatRequest,
    UpdateProductRequest,
    UpdateVendorRequest,
)
from models.common import Image, Name, Product
from utils.auth import create_token
from utils.http import Forbidden, InvalidRequest, NotFound, Unauthorized
from services.container import container
from services.ports import ImagesStoragePort, ProductsRepositoryPort, ReportsRepositoryPort, UsersRepositoryPort


class AuthService:
    def __init__(self) -> None:
        pass

    def login(self, email: str, password: str) -> TokenResponse:
        # Placeholder: in production integrate with Cognito or IdP
        # For now, accept any non-empty credentials and generate tokens for a dummy user ID
        if not email or not password:
            raise Unauthorized("Invalid credentials")
        user_id = uuid.uuid5(uuid.NAMESPACE_URL, f"user:{email}")
        access = create_token(str(user_id), settings().access_token_ttl, token_type="access")
        refresh = create_token(str(user_id), settings().refresh_token_ttl, token_type="refresh")
        return TokenResponse(user=user_id, accessToken=access, refreshToken=refresh, expiresIn=settings().access_token_ttl)

    def refresh(self, refresh_token: str) -> TokenResponse:
        from utils.auth import verify_token

        claims = verify_token(refresh_token, expected_typ="refresh")
        sub = claims["sub"]
        access = create_token(sub, settings().access_token_ttl, token_type="access")
        new_refresh = create_token(sub, settings().refresh_token_ttl, token_type="refresh")
        return TokenResponse(user=uuid.UUID(sub), accessToken=access, refreshToken=new_refresh, expiresIn=settings().access_token_ttl)

    def forgot(self, email: str) -> None:
        # No-op: would send email with reset link
        if not email:
            raise InvalidRequest("Email required")

    def reset(self, user: str, session: str, new_password: str) -> None:
        if not (user and session and new_password):
            raise InvalidRequest("Missing fields")


class UsersService:
    def __init__(self, repo: Optional[UsersRepositoryPort] = None) -> None:
        # Default to container-selected repo
        self.repo = repo or container().users_repo()

    def get(self, uid: str) -> Dict[str, Any]:
        return self.repo.get(uid)

    def list(self, limit: int, next_token: Optional[str]) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        return self.repo.list(limit, next_token)

    def create(self, username: str, email: str, role: str, preferences: Optional[Dict[str, str]]) -> Dict[str, Any]:
        uid = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        item = {
            "id": uid,
            "username": username,
            "email": email,
            "role": role,
            "preferences": preferences or {},
            "createdAt": now,
        }
        self.repo.put(item)
        return item

    def update(self, uid: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        item = self.repo.get(uid)
        item["updatedAt"] = datetime.now(timezone.utc).isoformat()
        for k, v in updates.items():
            if v is None:
                if k in item:
                    del item[k]
            else:
                item[k] = v
        self.repo.put(item)
        return item

    def delete(self, uid: str) -> None:
        self.repo.delete(uid)


class ProductsService:
    def __init__(self, repo: Optional[ProductsRepositoryPort] = None, images: Optional[ImagesStoragePort] = None) -> None:
        self.repo = repo or container().products_repo()
        self.images = images or container().images_store()

    def get(self, pid: str) -> Dict[str, Any]:
        return self.repo.get(pid)

    def create(self, req: CreateProductRequest) -> Dict[str, Any]:
        pid = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        item = {
            "id": pid,
            "name": req.name.model_dump(),
            "category": req.category,
            "formats": [],
            "images": [],
            "createdAt": now,
        }
        self.repo.put(item)
        return item

    def update(self, pid: str, req: UpdateProductRequest) -> Dict[str, Any]:
        item = self.repo.get(pid)
        item["updatedAt"] = datetime.now(timezone.utc).isoformat()
        if req.name is not None:
            # merge nullable fields
            for field, value in req.name.model_dump().items():
                if value is None:
                    item["name"].pop(field, None)
                else:
                    item["name"][field] = value
        if req.category is not None:
            for k, v in req.category.items():
                if v is None:
                    item["category"].pop(k, None)
                else:
                    item["category"][k] = v
        self.repo.put(item)
        return item

    def delete(self, pid: str) -> None:
        self.repo.delete(pid)

    def create_format(self, pid: str, req: CreateFormatRequest) -> Dict[str, Any]:
        item = self.repo.get(pid)
        fid = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        fmt: Dict[str, Any] = {"id": fid, "aspect": req.aspect, "createdAt": now}
        for d in ("length", "width", "thickness"):
            val = getattr(req, d)
            if val is not None:
                fmt[d] = val.model_dump()
        fmt["vendors"] = []
        item.setdefault("formats", []).append(fmt)
        item["updatedAt"] = now
        self.repo.put(item)
        return fmt

    def update_format(self, pid: str, fid: str, req: UpdateFormatRequest) -> Dict[str, Any]:
        item = self.repo.get(pid)
        formats = item.get("formats", [])
        fmt = next((f for f in formats if f["id"] == fid), None)
        if not fmt:
            raise NotFound("Format not found")
        now = datetime.now(timezone.utc).isoformat()
        if req.aspect is not None:
            fmt["aspect"] = req.aspect
        for d in ("length", "width", "thickness"):
            val = getattr(req, d)
            if val is None:
                # explicit removal
                if d in fmt:
                    del fmt[d]
            elif val is not None:
                fmt[d] = val.model_dump()
        fmt["updatedAt"] = now
        item["updatedAt"] = now
        self.repo.put(item)
        return fmt

    def delete_format(self, pid: str, fid: str) -> None:
        item = self.repo.get(pid)
        before = len(item.get("formats", []))
        item["formats"] = [f for f in item.get("formats", []) if f["id"] != fid]
        if len(item["formats"]) == before:
            raise NotFound("Format not found")
        item["updatedAt"] = datetime.now(timezone.utc).isoformat()
        self.repo.put(item)

    def create_vendor(self, pid: str, fid: str, req: CreateVendorRequest) -> Dict[str, Any]:
        item = self.repo.get(pid)
        formats = item.get("formats", [])
        fmt = next((f for f in formats if f["id"] == fid), None)
        if not fmt:
            raise NotFound("Format not found")
        vid = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        vendor = {"id": vid, **req.model_dump(exclude_none=True), "createdAt": now}
        fmt.setdefault("vendors", []).append(vendor)
        fmt["updatedAt"] = now
        item["updatedAt"] = now
        self.repo.put(item)
        return vendor

    def update_vendor(self, pid: str, fid: str, vid: str, req: UpdateVendorRequest) -> Dict[str, Any]:
        item = self.repo.get(pid)
        formats = item.get("formats", [])
        fmt = next((f for f in formats if f["id"] == fid), None)
        if not fmt:
            raise NotFound("Format not found")
        vendor = next((v for v in fmt.get("vendors", []) if v["id"] == vid), None)
        if not vendor:
            raise NotFound("Vendor not found")
        updates = req.model_dump()
        for k, v in updates.items():
            if v is None:
                vendor.pop(k, None)
            else:
                vendor[k] = v
        now = datetime.now(timezone.utc).isoformat()
        vendor["updatedAt"] = now
        fmt["updatedAt"] = now
        item["updatedAt"] = now
        self.repo.put(item)
        return vendor

    def delete_vendor(self, pid: str, fid: str, vid: str) -> None:
        item = self.repo.get(pid)
        formats = item.get("formats", [])
        fmt = next((f for f in formats if f["id"] == fid), None)
        if not fmt:
            raise NotFound("Format not found")
        before = len(fmt.get("vendors", []))
        fmt["vendors"] = [v for v in fmt.get("vendors", []) if v["id"] != vid]
        if len(fmt["vendors"]) == before:
            raise NotFound("Vendor not found")
        now = datetime.now(timezone.utc).isoformat()
        fmt["updatedAt"] = now
        item["updatedAt"] = now
        self.repo.put(item)

    def create_image(self, pid: str, image_bytes: bytes, mask_b64: str, hom_b64: str) -> Dict[str, Any]:
        # For now, simply accept image and store as-is PNG; parsing mask/hom is TODO
        if PILImage is None:
            raise InvalidRequest("Image processing not available")
        try:
            img = PILImage.open(io.BytesIO(image_bytes)).convert("RGB")
        except Exception as e:  # noqa: BLE001
            raise InvalidRequest("InvalidImageFormat") from e
        # normalize: convert to PNG
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        data = buf.getvalue()
        iid = str(uuid.uuid4())
        key = f"products/{pid}/images/{iid}.png"
        self.images.put_image(key, data, content_type="image/png")
        url = self.images.presign(key)
        # update product record
        item = self.repo.get(pid)
        now = datetime.now(timezone.utc).isoformat()
        image_obj = {"id": iid, "url": url, "createdAt": now}
        item.setdefault("images", []).append(image_obj)
        item["updatedAt"] = now
        self.repo.put(item)
        return image_obj

    def update_image(self, pid: str, iid: str, mask_b64: Optional[str], hom_b64: Optional[str]) -> Dict[str, Any]:
        # In a real impl, we would re-normalize using new metadata; for now just return existing
        item = self.repo.get(pid)
        img = next((i for i in item.get("images", []) if i["id"] == iid), None)
        if not img:
            raise NotFound("Image not found")
        img["updatedAt"] = datetime.now(timezone.utc).isoformat()
        item["updatedAt"] = img["updatedAt"]
        self.repo.put(item)
        return img

    def delete_image(self, pid: str, iid: str) -> None:
        item = self.repo.get(pid)
        before = len(item.get("images", []))
        item["images"] = [i for i in item.get("images", []) if i["id"] != iid]
        if len(item["images"]) == before:
            raise NotFound("Image not found")
        item["updatedAt"] = datetime.now(timezone.utc).isoformat()
        self.repo.put(item)


class ReportsService:
    def __init__(self, repo: Optional[ReportsRepositoryPort] = None, products: Optional[ProductsRepositoryPort] = None) -> None:
        self.repo = repo or container().reports_repo()
        self.products = products or container().products_repo()

    @staticmethod
    def _to_api_report(item: Dict[str, Any]) -> Dict[str, Any]:
        # Map storage field createdAt -> API field date
        api = dict(item)
        if "createdAt" in api:
            api["date"] = api.pop("createdAt")
        return api

    def list(self, requester: str, limit: int, next_token: Optional[str], everyone: bool) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        author = None if everyone else requester
        if author:
            items, nt = self.repo.list_by_author(author, limit, next_token)
            return [self._to_api_report(i) for i in items], nt
        # Admin list-all placeholder: not implemented; return empty for now
        return [], None

    def get(self, rid: str) -> Dict[str, Any]:
        item = self.repo.get(rid)
        return self._to_api_report(item)

    def create(self, author: str, title: str, reference: str) -> Dict[str, Any]:
        prod = self.products.get(reference)
        rid = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        item = {
            "id": rid,
            "author": author,
            "title": title,
            "createdAt": now,
            "reference": prod,
            "favorites": [],
        }
        self.repo.put(item)
        return self._to_api_report(item)

    def update(self, rid: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        item = self.repo.get(rid)
        if "reference" in updates:
            prod = self.products.get(updates["reference"])  # validate exists
            updates["reference"] = prod
        item.update({k: v for k, v in updates.items() if v is not None})
        item["updatedAt"] = datetime.now(timezone.utc).isoformat()
        self.repo.put(item)
        return self._to_api_report(item)

    def delete(self, rid: str) -> None:
        self.repo.delete(rid)

    def favorite(self, rid: str, pid: str, add: bool) -> None:
        item = self.repo.get(rid)
        prod = self.products.get(pid)
        favs = item.setdefault("favorites", [])
        exists = any(p["id"] == pid for p in favs)
        if add and not exists:
            favs.append(prod)
        if not add and exists:
            favs[:] = [p for p in favs if p["id"] != pid]
        item["updatedAt"] = datetime.now(timezone.utc).isoformat()
        self.repo.put(item)
