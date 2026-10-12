from shared.errors import (
    DomainForbidden,
    DomainNotFound,
    DomainRateLimited,
    DomainUnauthorized,
)
from shared.helpers import generate_subresource_id, require_admin
from shared.resolvers.http import Caller, HttpResolver
from shared.resolvers.http.errors import (
    Forbidden,
    NotFound,
    TooManyRequests,
    Unauthorized,
)
from shared.resolvers.http.responses import OK, NoContent

from .http import Request, Response
from .provider import Image, ProductImageProvider, UploadURL

__all__ = [
    "app",
    "lambda_handler",
]


app = HttpResolver(enable_validation=True)
provider = ProductImageProvider()
app.grant(*provider.permissions)


def lambda_handler(event, context):
    return app.resolve(event, context)


# ──── API Endpoints ───────────────────────────────────────────────────────────────────


@app.post(
    "/products/<id>/images",
    summary="Upload product image",
    description="Upload an image for a product. Requires admin role.",
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
) -> OK[Response.UploadURL] | Unauthorized | Forbidden | TooManyRequests:
    try:
        require_admin(caller)
        form = provider.upload_image(
            id=request.id,
            sid=generate_subresource_id(),
            format=request.format,
            hom=request.hom,
        )
        return OK(Response.UploadURL.model_validate(form))
    except DomainUnauthorized as exc:
        return Unauthorized(cause=exc)
    except DomainForbidden as exc:
        return Forbidden(cause=exc)
    except DomainRateLimited as exc:
        return TooManyRequests(cause=exc)


@app.patch(
    "/products/<id>/images/<sid>",
    summary="Transform product image",
    description="Mask and transform an image of a product. Requires admin role.",
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
    OK[Response.UploadURL]
    | OK[Response.Image]
    | Unauthorized
    | Forbidden
    | NotFound
    | TooManyRequests
):
    try:
        require_admin(caller)
        match provider.transform_image(
            id=request.id,
            sid=request.sid,
            format=request.format,
            hom=request.hom,
        ):
            case UploadURL() as form:
                return OK(Response.UploadURL.model_validate(form))
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
    description="Delete an image of a product. Requires admin role.",
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
