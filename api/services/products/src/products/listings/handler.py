from shared.errors import (
    DomainForbidden,
    DomainNotFound,
    DomainRateLimited,
    DomainUnauthorized,
)
from shared.helpers import generate_subresource_id, require_admin
from shared.http import Caller, HttpResolver
from shared.http.errors import Forbidden, NotFound, TooManyRequests, Unauthorized
from shared.http.responses import OK, Created, NoContent

from .http import Request, Response
from .provider import ProductListingProvider

__all__ = [
    "app",
    "lambda_handler",
]


app = HttpResolver(enable_validation=True)
provider = ProductListingProvider()
app.grant(*provider.permissions)


def lambda_handler(event, context):
    return app.resolve(event, context)


# ──── API Endpoints ───────────────────────────────────────────────────────────────────


@app.post(
    "/products/<id>/listings",
    summary="Create product listing",
    description="Create a listing for a product. Requires admin role.",
    tags=["product", "listing"],
    responses={
        201: "Product listing created",
        401: "Authentication required",
        403: "Access denied",
        429: "Too many requests",
    },
)
def create(
    caller: Caller,
    request: Request.Create,
) -> Created[Response.Listing] | Unauthorized | Forbidden | TooManyRequests:
    try:
        require_admin(caller)
        listing = provider.create_listing(
            id=request.id,
            sid=generate_subresource_id(),
            vendor=request.vendor,
            sku=request.sku,
            name=request.name,
            prices=request.prices,
            url=request.url,
        )
        return Created(Response.Listing.model_validate(listing))
    except DomainUnauthorized as exc:
        return Unauthorized(cause=exc)
    except DomainForbidden as exc:
        return Forbidden(cause=exc)
    except DomainRateLimited as exc:
        return TooManyRequests(cause=exc)


@app.patch(
    "/products/<id>/listings/<sid>",
    summary="Update product listing",
    description="Update a listing for a product. Requires admin role.",
    tags=["product", "listing"],
    responses={
        200: "Product listing updated",
        401: "Authentication required",
        403: "Access denied",
        404: "Product listing not found",
        429: "Too many requests",
    },
)
def update(
    caller: Caller,
    request: Request.Update,
) -> OK[Response.Listing] | Unauthorized | Forbidden | NotFound | TooManyRequests:
    try:
        require_admin(caller)
        listing = provider.update_listing(
            id=request.id,
            sid=request.sid,
            vendor=request.vendor,
            sku=request.sku,
            name=request.name,
            prices=request.prices,
            url=request.url,
        )
        return OK(Response.Listing.model_validate(listing))
    except DomainUnauthorized as exc:
        return Unauthorized(cause=exc)
    except DomainForbidden as exc:
        return Forbidden(cause=exc)
    except DomainNotFound as exc:
        return NotFound(cause=exc)
    except DomainRateLimited as exc:
        return TooManyRequests(cause=exc)


@app.delete(
    "/products/<id>/listings/<sid>",
    summary="Delete product listing",
    description="Delete a listing for a product. Requires admin role.",
    tags=["product", "listing"],
    responses={
        200: "Product listing deleted",
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
        provider.delete_listing(
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
