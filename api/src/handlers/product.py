from __future__ import annotations

import base64
import json
import re
from typing import Any, Dict

from models.api import (
    CreateFormatRequest,
    CreateProductRequest,
    CreateVendorRequest,
    UpdateFormatRequest,
    UpdateProductRequest,
    UpdateVendorRequest,
)
from services.service import ProductsService
from utils.auth import get_auth_claims
from utils.http import InvalidRequest, no_content, response


svc = ProductsService()


def handle_product(event: Dict[str, Any]) -> Dict[str, Any]:
    path = event.get("rawPath") or event.get("path", "")
    method = (event.get("requestContext", {}).get("http", {}) or {}).get("method") or event.get("httpMethod")
    # auth (supports API GW authorizer or Bearer)
    _claims = get_auth_claims(event, expected_typ="access")

    m = re.fullmatch(r"/product(?:/([0-9a-fA-F-]+)(?:/(format)(?:/([0-9a-fA-F-]+)(?:/(vendor)(?:/([0-9a-fA-F-]+))?)?)?)?(?:/(image)(?:/([0-9a-fA-F-]+))?)?)?", path)
    if not m:
        raise InvalidRequest("Invalid product route")
    pid, fmt_kw, fid, ven_kw, vid, img_kw, iid = m.groups()

    # Body
    raw_body = event.get("body")
    if raw_body and event.get("isBase64Encoded"):
        raw_body = base64.b64decode(raw_body)
        try:
            raw_body = raw_body.decode("utf-8")
        except Exception:  # noqa: BLE001
            # keep bytes for multipart
            pass
    data = {}
    if not (img_kw == "image" and method == "POST"):
        # non-multipart or JSON payloads
        data = json.loads(raw_body or "{}") if isinstance(raw_body, str) else {}

    if path == "/product" and method == "POST":
        req = CreateProductRequest.model_validate(data)
        item = svc.create(req)
        return response(201, item)

    if pid and not fmt_kw and not img_kw:
        if method == "GET":
            item = svc.get(pid)
            return response(200, item)
        if method == "PATCH":
            req = UpdateProductRequest.model_validate(data)
            item = svc.update(pid, req)
            return response(200, item)
        if method == "DELETE":
            svc.delete(pid)
            return no_content()

    if pid and fmt_kw == "format" and not fid and method == "POST":
        req = CreateFormatRequest.model_validate(data)
        fmt = svc.create_format(pid, req)
        return response(201, fmt)

    if pid and fmt_kw == "format" and fid and not ven_kw and method == "PATCH":
        req = UpdateFormatRequest.model_validate(data)
        fmt = svc.update_format(pid, fid, req)
        return response(200, fmt)

    if pid and fmt_kw == "format" and fid and not ven_kw and method == "DELETE":
        svc.delete_format(pid, fid)
        return no_content()

    if pid and fmt_kw == "format" and fid and ven_kw == "vendor" and not vid and method == "POST":
        req = CreateVendorRequest.model_validate(data)
        ven = svc.create_vendor(pid, fid, req)
        return response(201, ven)

    if pid and fmt_kw == "format" and fid and ven_kw == "vendor" and vid and method == "PATCH":
        req = UpdateVendorRequest.model_validate(data)
        ven = svc.update_vendor(pid, fid, vid, req)
        return response(200, ven)

    if pid and fmt_kw == "format" and fid and ven_kw == "vendor" and vid and method == "DELETE":
        svc.delete_vendor(pid, fid, vid)
        return no_content()

    # Image upload and update
    if pid and img_kw == "image" and not iid and method == "POST":
        # Expect multipart/form-data: not fully parsed here; assume API Gateway HTTP API with base64 body
        # For simplicity in this scaffold, allow JSON with base64 fields as well
        ctype = (event.get("headers") or {}).get("content-type") or (event.get("headers") or {}).get("Content-Type")
        if ctype and ctype.startswith("multipart/"):
            # Implementing robust multipart parsing in Lambda requires parsing; omitted in scaffold
            raise InvalidRequest("Multipart upload not supported in scaffold; send JSON with base64 fields")
        payload = json.loads(raw_body or "{}")
        image_b64 = payload.get("image")
        mask_b64 = payload.get("mask")
        hom_b64 = payload.get("hom")
        if not image_b64 or not mask_b64 or not hom_b64:
            raise InvalidRequest("image, mask, hom are required")
        image_bytes = base64.b64decode(image_b64)
        img = svc.create_image(pid, image_bytes, mask_b64, hom_b64)
        return response(201, img)

    if pid and img_kw == "image" and iid and method == "PATCH":
        payload = json.loads(raw_body or "{}")
        mask_b64 = payload.get("mask")
        hom_b64 = payload.get("hom")
        img = svc.update_image(pid, iid, mask_b64, hom_b64)
        return response(200, img)

    if pid and img_kw == "image" and iid and method == "DELETE":
        svc.delete_image(pid, iid)
        return no_content()

    raise InvalidRequest("Unsupported product route")
