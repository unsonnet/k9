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

    fields = read_multipart_body(event)

    # image is required per spec
    if "image" not in fields:
        raise BadRequest("image required")

    _, image_bytes = fields["image"]

    # mask and hom are optional
    mask_bytes = fields.get("mask", (None, b""))[1]
    hom_bytes = fields.get("hom", (None, b""))[1]

    # Treat empty text as None
    mask_str = mask_bytes.decode("utf-8") if mask_bytes else None
    hom_str = hom_bytes.decode("utf-8") if hom_bytes else None

    req = ImageUploadRequest(
        image=image_bytes,
        mask=mask_str,
        hom=hom_str,
    )

    return svc.upload_image(ctx, pid, req)


@router.route("/{productId}/image/{imageId}", method="PATCH")
def update_image(
    event: Mapping[str, Any], params: Mapping[str, str]
) -> HttpResponse[Any]:
    ctx = _ctx(event)
    pid = UUID(params["productId"])
    iid = UUID(params["imageId"])
    data = read_json_body(event)
    req = ImageUpdateRequest.model_validate(data)
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
