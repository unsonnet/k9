from __future__ import annotations

from typing import Any, Mapping
from uuid import UUID

from utils.http import (
    HttpResponse,
    BadRequest,
    read_bearer_token,
    read_json_body,
    read_multipart_body,
)
from utils.routing import Router
from models.auth import AuthContext
from models.product import (
    CreateFormatRequest,
    CreateProductRequest,
    CreateVendorRequest,
    ImageUpdateRequest,
    ImageUploadRequest,
    UpdateFormatRequest,
    UpdateProductRequest,
    UpdateVendorRequest,
)
from services.product import ProductService

router = Router(prefix="/product")
svc = ProductService()


def _ctx(event: Mapping[str, Any]) -> AuthContext:
    token = read_bearer_token(event)
    if not token:
        raise BadRequest("Missing Authorization header")
    return AuthContext(bearerToken=token)


# --- /product


@router.route("", method="POST")
def create_product(event: Mapping[str, Any]) -> HttpResponse[Any]:
    ctx = _ctx(event)
    data = read_json_body(event)
    req = CreateProductRequest.model_validate(data)
    return svc.create_product(ctx, req)


# --- /product/{productId}


@router.route("/{productId}", method="GET")
def get_product(
    event: Mapping[str, Any], params: Mapping[str, str]
) -> HttpResponse[Any]:
    ctx = _ctx(event)
    pid = UUID(params["productId"])
    return svc.get_product(ctx, pid)


@router.route("/{productId}", method="PATCH")
def update_product(
    event: Mapping[str, Any], params: Mapping[str, str]
) -> HttpResponse[Any]:
    ctx = _ctx(event)
    pid = UUID(params["productId"])
    data = read_json_body(event)
    req = UpdateProductRequest.model_validate(data)
    return svc.update_product(ctx, pid, req)


@router.route("/{productId}", method="DELETE")
def delete_product(
    event: Mapping[str, Any], params: Mapping[str, str]
) -> HttpResponse[Any]:
    ctx = _ctx(event)
    pid = UUID(params["productId"])
    return svc.delete_product(ctx, pid)


# --- /product/{productId}/format


@router.route("/{productId}/format", method="POST")
def create_format(
    event: Mapping[str, Any], params: Mapping[str, str]
) -> HttpResponse[Any]:
    ctx = _ctx(event)
    pid = UUID(params["productId"])
    data = read_json_body(event)
    req = CreateFormatRequest.model_validate(data)
    return svc.create_format(ctx, pid, req)


@router.route("/{productId}/format/{formatId}", method="PATCH")
def update_format(
    event: Mapping[str, Any], params: Mapping[str, str]
) -> HttpResponse[Any]:
    ctx = _ctx(event)
    pid = UUID(params["productId"])
    fid = UUID(params["formatId"])
    data = read_json_body(event)
    req = UpdateFormatRequest.model_validate(data)
    return svc.update_format(ctx, pid, fid, req)


@router.route("/{productId}/format/{formatId}", method="DELETE")
def delete_format(
    event: Mapping[str, Any], params: Mapping[str, str]
) -> HttpResponse[Any]:
    ctx = _ctx(event)
    pid = UUID(params["productId"])
    fid = UUID(params["formatId"])
    return svc.delete_format(ctx, pid, fid)


# --- /product/{productId}/format/{formatId}/vendor


@router.route("/{productId}/format/{formatId}/vendor", method="POST")
def create_vendor(
    event: Mapping[str, Any], params: Mapping[str, str]
) -> HttpResponse[Any]:
    ctx = _ctx(event)
    pid = UUID(params["productId"])
    fid = UUID(params["formatId"])
    data = read_json_body(event)
    req = CreateVendorRequest.model_validate(data)
    return svc.create_vendor(ctx, pid, fid, req)


@router.route("/{productId}/format/{formatId}/vendor/{vendorId}", method="PATCH")
def update_vendor(
    event: Mapping[str, Any], params: Mapping[str, str]
) -> HttpResponse[Any]:
    ctx = _ctx(event)
    pid = UUID(params["productId"])
    fid = UUID(params["formatId"])
    vid = UUID(params["vendorId"])
    data = read_json_body(event)
    req = UpdateVendorRequest.model_validate(data)
    return svc.update_vendor(ctx, pid, fid, vid, req)


@router.route("/{productId}/format/{formatId}/vendor/{vendorId}", method="DELETE")
def delete_vendor(
    event: Mapping[str, Any], params: Mapping[str, str]
) -> HttpResponse[Any]:
    ctx = _ctx(event)
    pid = UUID(params["productId"])
    fid = UUID(params["formatId"])
    vid = UUID(params["vendorId"])
    return svc.delete_vendor(ctx, pid, fid, vid)


# --- /product/{productId}/image


@router.route("/{productId}/image", method="POST")
def upload_image(
    event: Mapping[str, Any], params: Mapping[str, str]
) -> HttpResponse[Any]:
    ctx = _ctx(event)
    pid = UUID(params["productId"])

    parts = read_multipart_body(event)
    if parts is None:
        raise BadRequest("multipart/form-data required")

    # required
    if "image" not in parts:
        raise BadRequest("image required")
    _, image_bytes = parts["image"]

    # optional binary fields (raw bytes, no decoding)
    _, mask_bytes = parts.get("mask", (None, None))
    _, hom_bytes = parts.get("hom", (None, None))

    req = ImageUploadRequest(
        image=image_bytes,
        mask=mask_bytes,
        hom=hom_bytes,
    )
    return svc.upload_image(ctx, pid, req)


@router.route("/{productId}/image/{imageId}", method="PATCH")
def update_image(
    event: Mapping[str, Any], params: Mapping[str, str]
) -> HttpResponse[Any]:
    ctx = _ctx(event)
    pid = UUID(params["productId"])
    iid = UUID(params["imageId"])

    parts = read_multipart_body(event)
    if parts is None:
        raise BadRequest("multipart/form-data required")

    _, mask_bytes = parts.get("mask", (None, None))
    _, hom_bytes = parts.get("hom", (None, None))

    reset = False
    if "reset" in parts:
        _, raw = parts["reset"]
        if raw is None:
            raise BadRequest("reset provided but empty")
        val = raw.decode("utf-8").strip().lower()
        if val == "true":
            reset = True
        elif val == "false":
            reset = False
        else:
            raise BadRequest("reset must be 'true' or 'false'")

    req = ImageUpdateRequest(
        reset=reset,
        mask=mask_bytes,
        hom=hom_bytes,
    )
    return svc.update_image(ctx, pid, iid, req)


@router.route("/{productId}/image/{imageId}", method="DELETE")
def delete_image(
    event: Mapping[str, Any], params: Mapping[str, str]
) -> HttpResponse[Any]:
    ctx = _ctx(event)
    pid = UUID(params["productId"])
    iid = UUID(params["imageId"])
    return svc.delete_image(ctx, pid, iid)


def lambda_handler(event, context):
    return router.dispatch(event)
