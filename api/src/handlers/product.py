from __future__ import annotations

import base64
from typing import Any, Mapping
from uuid import UUID

from utils.http import (
    BadRequest,
    Created,
    NoContent,
    OK,
    read_bearer_token,
    read_json_body,
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
from services.product.service import ProductService

router = Router(prefix="/product")
svc = ProductService()


def _ctx(event: Mapping[str, Any]) -> AuthContext:
    token = read_bearer_token(event)
    if not token:
        raise BadRequest("Missing Authorization header")
    return AuthContext(bearerToken=token)


# --- /product


@router.route("", method="POST")
def create_product(event: Mapping[str, Any]) -> Created[Any]:
    ctx = _ctx(event)
    data = read_json_body(event)
    req = CreateProductRequest.model_validate(data)
    return Created(svc.create_product(ctx, req))


# --- /product/{productId}


@router.route("/{productId}", method="GET")
def get_product(event: Mapping[str, Any], params: Mapping[str, str]) -> OK[Any]:
    ctx = _ctx(event)
    pid = UUID(params["productId"])
    return OK(svc.get_product(ctx, pid))


@router.route("/{productId}", method="PATCH")
def update_product(event: Mapping[str, Any], params: Mapping[str, str]) -> OK[Any]:
    ctx = _ctx(event)
    pid = UUID(params["productId"])
    data = read_json_body(event)
    req = UpdateProductRequest.model_validate(data)
    return OK(svc.update_product(ctx, pid, req))


@router.route("/{productId}", method="DELETE")
def delete_product(event: Mapping[str, Any], params: Mapping[str, str]) -> NoContent:
    ctx = _ctx(event)
    pid = UUID(params["productId"])
    svc.delete_product(ctx, pid)
    return NoContent()


# --- /product/{productId}/format


@router.route("/{productId}/format", method="POST")
def create_format(event: Mapping[str, Any], params: Mapping[str, str]) -> Created[Any]:
    ctx = _ctx(event)
    pid = UUID(params["productId"])
    data = read_json_body(event)
    req = CreateFormatRequest.model_validate(data)
    return Created(svc.create_format(ctx, pid, req))


# --- /product/{productId}/format/{formatId}


@router.route("/{productId}/format/{formatId}", method="PATCH")
def update_format(event: Mapping[str, Any], params: Mapping[str, str]) -> OK[Any]:
    ctx = _ctx(event)
    pid = UUID(params["productId"])
    fid = UUID(params["formatId"])
    data = read_json_body(event)
    req = UpdateFormatRequest.model_validate(data)
    return OK(svc.update_format(ctx, pid, fid, req))


@router.route("/{productId}/format/{formatId}", method="DELETE")
def delete_format(event: Mapping[str, Any], params: Mapping[str, str]) -> NoContent:
    ctx = _ctx(event)
    pid = UUID(params["productId"])
    fid = UUID(params["formatId"])
    svc.delete_format(ctx, pid, fid)
    return NoContent()


# --- /product/{productId}/format/{formatId}/vendor


@router.route("/{productId}/format/{formatId}/vendor", method="POST")
def create_vendor(event: Mapping[str, Any], params: Mapping[str, str]) -> Created[Any]:
    ctx = _ctx(event)
    pid = UUID(params["productId"])
    fid = UUID(params["formatId"])
    data = read_json_body(event)
    req = CreateVendorRequest.model_validate(data)
    return Created(svc.create_vendor(ctx, pid, fid, req))


# --- /product/{productId}/format/{formatId}/vendor/{vendorId}


@router.route("/{productId}/format/{formatId}/vendor/{vendorId}", method="PATCH")
def update_vendor(event: Mapping[str, Any], params: Mapping[str, str]) -> OK[Any]:
    ctx = _ctx(event)
    pid = UUID(params["productId"])
    fid = UUID(params["formatId"])
    vid = UUID(params["vendorId"])
    data = read_json_body(event)
    req = UpdateVendorRequest.model_validate(data)
    return OK(svc.update_vendor(ctx, pid, fid, vid, req))


@router.route("/{productId}/format/{formatId}/vendor/{vendorId}", method="DELETE")
def delete_vendor(event: Mapping[str, Any], params: Mapping[str, str]) -> NoContent:
    ctx = _ctx(event)
    pid = UUID(params["productId"])
    fid = UUID(params["formatId"])
    vid = UUID(params["vendorId"])
    svc.delete_vendor(ctx, pid, fid, vid)
    return NoContent()


# --- /product/{productId}/image


@router.route("/{productId}/image", method="POST")
def upload_image(event: Mapping[str, Any], params: Mapping[str, str]) -> Created[Any]:
    ctx = _ctx(event)
    pid = UUID(params["productId"])
    data = read_json_body(event)

    image_b64 = data.get("image")
    mask_b64 = data.get("mask")
    hom_b64 = data.get("hom")
    if not image_b64 or not mask_b64 or not hom_b64:
        raise BadRequest("image, mask, hom are required")

    image_bytes = base64.b64decode(image_b64)
    req = ImageUploadRequest(image_bytes=image_bytes, mask=mask_b64, hom=hom_b64)
    return Created(svc.upload_image(ctx, pid, req))


# --- /product/{productId}/image/{imageId}


@router.route("/{productId}/image/{imageId}", method="PATCH")
def update_image(event: Mapping[str, Any], params: Mapping[str, str]) -> OK[Any]:
    ctx = _ctx(event)
    pid = UUID(params["productId"])
    iid = UUID(params["imageId"])
    data = read_json_body(event)
    req = ImageUpdateRequest.model_validate(data)
    return OK(svc.update_image(ctx, pid, iid, req))


@router.route("/{productId}/image/{imageId}", method="DELETE")
def delete_image(event: Mapping[str, Any], params: Mapping[str, str]) -> NoContent:
    ctx = _ctx(event)
    pid = UUID(params["productId"])
    iid = UUID(params["imageId"])
    svc.delete_image(ctx, pid, iid)
    return NoContent()


def lambda_handler(event, context):
    return router.dispatch(event)
