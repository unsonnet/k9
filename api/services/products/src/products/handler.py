from shared.errors import (
    DomainForbidden,
    DomainNotFound,
    DomainRateLimited,
    DomainUnauthorized,
)
from shared.helpers import generate_resource_id, require_admin
from shared.http import Caller, HttpResolver
from shared.http.errors import Forbidden, NotFound, TooManyRequests, Unauthorized
from shared.http.responses import OK, Created, NoContent

from .http import Request, Response
from .provider import ProductProvider

__all__ = [
    "app",
    "lambda_handler",
]


app = HttpResolver(enable_validation=True)
provider = ProductProvider()
app.grant(*provider.permissions)


def lambda_handler(event, context):
    return app.resolve(event, context)


# ──── API Endpoints ───────────────────────────────────────────────────────────────────


@app.post(
    "/products",
    summary="Create product",
    description="Create a product. Requires admin role.",
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
    request: Request.Create,
) -> Created[Response.Product] | Unauthorized | Forbidden | TooManyRequests:
    try:
        require_admin(caller)
        product = provider.create_product(
            id=generate_resource_id(),
            brand=request.brand,
            material=request.material,
            format=request.format,
            subformats=request.subformats,
            meta=request.meta,
        )
        return Created(Response.Product.model_validate(product))
    except DomainUnauthorized as exc:
        return Unauthorized(cause=exc)
    except DomainForbidden as exc:
        return Forbidden(cause=exc)
    except DomainRateLimited as exc:
        return TooManyRequests(cause=exc)


@app.get(
    "/products/<id>",
    summary="Read product",
    description="Read a product.",
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
    request: Request.Read,
) -> OK[Response.Product] | Unauthorized | NotFound | TooManyRequests:
    try:
        product = provider.read_product(
            id=request.id,
        )
        return OK(Response.Product.model_validate(product))
    except DomainUnauthorized as exc:
        return Unauthorized(cause=exc)
    except DomainNotFound as exc:
        return NotFound(cause=exc)
    except DomainRateLimited as exc:
        return TooManyRequests(cause=exc)


@app.patch(
    "/products/<id>",
    summary="Update product",
    description="Update a product. Requires admin role.",
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
    request: Request.Update,
) -> OK[Response.Product] | Unauthorized | Forbidden | NotFound | TooManyRequests:
    try:
        require_admin(caller)
        product = provider.update_product(
            id=request.id,
            brand=request.brand,
            material=request.material,
            format=request.format,
            subformats=request.subformats,
            meta=request.meta,
        )
        return OK(Response.Product.model_validate(product))
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
    description="Delete a product. Requires admin role.",
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
    request: Request.Delete,
) -> NoContent | Unauthorized | Forbidden | TooManyRequests:
    try:
        require_admin(caller)
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
