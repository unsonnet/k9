from k9.resolvers.http.errors import Forbidden, NotFound, TooManyRequests, Unauthorized
from k9.resolvers.http.responses import OK, Created, NoContent
from k9.types.common import Caller, ResourceID
from k9.types.errors import (
    DomainForbidden,
    DomainNotFound,
    DomainRateLimited,
    DomainUnauthorized,
)

from . import app
from .http import Create, Delete, Read, Update
from .provider import Product, ProductProvider

provider = ProductProvider()
app.grant(*provider.permissions)


@app.post(
    "/products",
    summary="Create product",
    tags=["product"],
    responses={
        201: "Product created",
        401: "Authentication required",
        403: "Access denied",
        429: "Too many requests",
    },
)
def create(
    caller: Caller,
    request: Create,
) -> Created[Product] | Unauthorized | Forbidden | TooManyRequests:
    try:
        caller.require_admin()
        product = provider.create_product(
            id=ResourceID.random(),
            scope=request.scope,
            brand=request.brand,
            material=request.material,
            format=request.format,
            subformats=request.subformats,
            meta=request.meta,
        )
        return Created(product)
    except DomainUnauthorized as exc:
        return Unauthorized(cause=exc)
    except DomainForbidden as exc:
        return Forbidden(cause=exc)
    except DomainRateLimited as exc:
        return TooManyRequests(cause=exc)


@app.get(
    "/products/<id>",
    summary="Read product",
    tags=["product"],
    responses={
        200: "Product found",
        401: "Authentication required",
        404: "Product not found",
        429: "Too many requests",
    },
)
def read(
    caller: Caller,
    request: Read,
) -> OK[Product] | Unauthorized | NotFound | TooManyRequests:
    try:
        product = provider.read_product(
            id=request.id,
        )
        return OK(product)
    except DomainUnauthorized as exc:
        return Unauthorized(cause=exc)
    except DomainNotFound as exc:
        return NotFound(cause=exc)
    except DomainRateLimited as exc:
        return TooManyRequests(cause=exc)


@app.patch(
    "/products/<id>",
    summary="Update product",
    tags=["product"],
    responses={
        200: "Product updated",
        401: "Authentication required",
        403: "Access denied",
        404: "Product not found",
        429: "Too many requests",
    },
)
def update(
    caller: Caller,
    request: Update,
) -> OK[Product] | Unauthorized | Forbidden | NotFound | TooManyRequests:
    try:
        caller.require_admin()
        product = provider.update_product(
            id=request.id,
            scope=request.scope,
            brand=request.brand,
            material=request.material,
            format=request.format,
            subformats=request.subformats,
            meta=request.meta,
        )
        return OK(product)
    except DomainUnauthorized as exc:
        return Unauthorized(cause=exc)
    except DomainForbidden as exc:
        return Forbidden(cause=exc)
    except DomainNotFound as exc:
        return NotFound(cause=exc)
    except DomainRateLimited as exc:
        return TooManyRequests(cause=exc)


@app.delete(
    "/products/<id>",
    summary="Delete product",
    tags=["product"],
    responses={
        200: "Product deleted",
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
        provider.delete_product(
            id=request.id,
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
