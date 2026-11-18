from k9.resolvers.http.errors import Forbidden, NotFound, TooManyRequests, Unauthorized
from k9.resolvers.http.responses import OK, NoContent
from k9.types.common import Caller, SubresourceID
from k9.types.errors import (
    DomainForbidden,
    DomainNotFound,
    DomainRateLimited,
    DomainUnauthorized,
)

from .. import app
from .http import Delete, Transform, Upload
from .provider import Image, ImageProvider, UploadForm

provider = ImageProvider()
app.grant(*provider.permissions)


@app.post(
    "/products/<id>/images",
    summary="Upload product image",
    tags=["product", "image"],
    responses={
        201: "Product image uploaded",
        401: "Authentication required",
        403: "Access denied",
        429: "Too many requests",
    },
)
def upload(
    caller: Caller,
    request: Upload,
) -> OK[UploadForm] | Unauthorized | Forbidden | TooManyRequests:
    try:
        caller.require_admin()
        form = provider.create_image(
            id=request.id,
            sid=SubresourceID.random(),
            scope=request.scope,
            format=request.format,
            length=request.length,
            hom=request.hom,
        )
        return OK(form)
    except DomainUnauthorized as exc:
        return Unauthorized(cause=exc)
    except DomainForbidden as exc:
        return Forbidden(cause=exc)
    except DomainRateLimited as exc:
        return TooManyRequests(cause=exc)


@app.patch(
    "/products/<id>/images/<sid>",
    summary="Transform product image",
    tags=["product", "image"],
    responses={
        200: "Product image transformed",
        401: "Authentication required",
        403: "Access denied",
        404: "Product image not found",
        429: "Too many requests",
    },
)
def transform(
    caller: Caller,
    request: Transform,
) -> OK[UploadForm] | OK[Image] | Unauthorized | Forbidden | NotFound | TooManyRequests:
    try:
        caller.require_admin()
        match provider.update_image(
            id=request.id,
            sid=request.sid,
            scope=request.scope,
            format=request.format,
            length=request.length,
            hom=request.hom,
        ):
            case UploadForm() as form:
                return OK(form)
            case Image() as image:
                return OK(image)
    except DomainUnauthorized as exc:
        return Unauthorized(cause=exc)
    except DomainForbidden as exc:
        return Forbidden(cause=exc)
    except DomainNotFound as exc:
        return NotFound(cause=exc)
    except DomainRateLimited as exc:
        return TooManyRequests(cause=exc)


@app.delete(
    "/products/<id>/images/<sid>",
    summary="Delete product image",
    tags=["product", "image"],
    responses={
        200: "Product image deleted",
        401: "Authentication required",
        403: "Access denied",
        429: "Too many requests",
    },
)
def delete(
    caller: Caller,
    request: Delete,
) -> NoContent | Unauthorized | Forbidden | TooManyRequests:
    try:
        caller.require_admin()
        provider.delete_image(
            id=request.id,
            sid=request.sid,
        )
        return NoContent()
    except DomainNotFound:
        return NoContent()
    except DomainUnauthorized as exc:
        return Unauthorized(cause=exc)
    except DomainForbidden as exc:
        return Forbidden(cause=exc)
    except DomainRateLimited as exc:
        return TooManyRequests(cause=exc)
