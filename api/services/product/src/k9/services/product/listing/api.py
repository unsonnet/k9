from k9.resolvers.http.errors import Forbidden, NotFound, TooManyRequests, Unauthorized
from k9.resolvers.http.responses import OK, Created, NoContent
from k9.types.common import Caller, SubresourceID
from k9.types.errors import (
    DomainForbidden,
    DomainNotFound,
    DomainRateLimited,
    DomainUnauthorized,
)

from .. import app
from .http import Create, Delete, Update
from .provider import Listing, ListingProvider

provider = ListingProvider()
app.grant(*provider.permissions)


@app.post(
    "/products/<id>/listings",
    summary="Create product listing",
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
    request: Create,
) -> Created[Listing] | Unauthorized | Forbidden | TooManyRequests:
    try:
        caller.require_admin()
        listing = provider.create_listing(
            id=request.id,
            sid=SubresourceID.random(),
            scope=request.scope,
            vendor=request.vendor,
            sku=request.sku,
            name=request.name,
            website=request.website,
        )
        return Created(listing)
    except DomainUnauthorized as exc:
        return Unauthorized(cause=exc)
    except DomainForbidden as exc:
        return Forbidden(cause=exc)
    except DomainRateLimited as exc:
        return TooManyRequests(cause=exc)


@app.patch(
    "/products/<id>/listings/<sid>",
    summary="Update product listing",
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
    request: Update,
) -> OK[Listing] | Unauthorized | Forbidden | NotFound | TooManyRequests:
    try:
        caller.require_admin()
        listing = provider.update_listing(
            id=request.id,
            sid=request.sid,
            scope=request.scope,
            vendor=request.vendor,
            sku=request.sku,
            name=request.name,
            website=request.website,
        )
        return OK(listing)
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
    request: Delete,
) -> NoContent | Unauthorized | Forbidden | TooManyRequests:
    try:
        caller.require_admin()
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
