from k9.resolvers.http.errors import (
    Forbidden,
    NotFound,
    TooManyRequests,
    Unauthorized,
)
from k9.resolvers.http.responses import OK, NoContent
from k9.shared.errors import (
    DomainForbidden,
    DomainNotFound,
    DomainRateLimited,
    DomainUnauthorized,
)
from k9.shared.helpers import generate_subresource_id, require_admin
from k9.shared.types import Caller

from .. import app
from .http import Request, Response
from .provider import Image, ImageProvider, Upload

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
    request: Request.Upload,
) -> OK[Response.Upload] | Unauthorized | Forbidden | TooManyRequests:
    try:
        require_admin(caller)
        form = provider.create_image(
            id=request.id,
            sid=generate_subresource_id(),
            scope=request.scope,
            format=request.format,
            length=request.length,
            hom=request.hom,
        )
        return OK(Response.Upload.model_validate(form))
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
    request: Request.Transform,
) -> (
    OK[Response.Upload]
    | OK[Response.Image]
    | Unauthorized
    | Forbidden
    | NotFound
    | TooManyRequests
):
    try:
        require_admin(caller)
        match provider.update_image(
            id=request.id,
            sid=request.sid,
            scope=request.scope,
            format=request.format,
            length=request.length,
            hom=request.hom,
        ):
            case Upload() as form:
                return OK(Response.Upload.model_validate(form))
            case Image() as image:
                return OK(Response.Image.model_validate(image))
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
    request: Request.Delete,
) -> NoContent | Unauthorized | Forbidden | TooManyRequests:
    try:
        require_admin(caller)
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
