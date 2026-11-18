from k9.resolvers.http.errors import Forbidden, NotFound, TooManyRequests, Unauthorized
from k9.resolvers.http.responses import OK, Created, NoContent
from k9.types.common import Caller
from k9.types.errors import (
    DomainForbidden,
    DomainNotFound,
    DomainRateLimited,
    DomainUnauthorized,
)

from ... import app
from .http import Create, Delete, Update
from .provider import Price, PriceProvider

provider = PriceProvider()
app.grant(*provider.permissions)


@app.post(
    "/products/<id>/listings/<sid>/prices/<date>",
    summary="Create product listing price",
    tags=["product", "listing", "price"],
    responses={
        201: "Product listing price created",
        401: "Authentication required",
        403: "Access denied",
        429: "Too many requests",
    },
)
def create(
    caller: Caller,
    request: Create,
) -> Created[Price] | Unauthorized | Forbidden | TooManyRequests:
    try:
        caller.require_admin()
        price = provider.create_price(
            id=request.id,
            sid=request.sid,
            date=request.date,
            scope=request.scope,
            currency=request.currency,
            rate=request.rate,
            unit=request.unit,
            stock=request.stock,
        )
        return Created(price)
    except DomainUnauthorized as exc:
        return Unauthorized(cause=exc)
    except DomainForbidden as exc:
        return Forbidden(cause=exc)
    except DomainRateLimited as exc:
        return TooManyRequests(cause=exc)


@app.patch(
    "/products/<id>/listings/<sid>/prices/<date>",
    summary="Update product listing price",
    tags=["product", "listing", "price"],
    responses={
        200: "Product listing price updated",
        401: "Authentication required",
        403: "Access denied",
        404: "Product listing price not found",
        429: "Too many requests",
    },
)
def update(
    caller: Caller,
    request: Update,
) -> OK[Price] | Unauthorized | Forbidden | NotFound | TooManyRequests:
    try:
        caller.require_admin()
        price = provider.update_price(
            id=request.id,
            sid=request.sid,
            date=request.date,
            scope=request.scope,
            currency=request.currency,
            rate=request.rate,
            unit=request.unit,
            stock=request.stock,
        )
        return OK(price)
    except DomainUnauthorized as exc:
        return Unauthorized(cause=exc)
    except DomainForbidden as exc:
        return Forbidden(cause=exc)
    except DomainNotFound as exc:
        return NotFound(cause=exc)
    except DomainRateLimited as exc:
        return TooManyRequests(cause=exc)


@app.delete(
    "/products/<id>/listings/<sid>/prices/<date>",
    summary="Delete product listing price",
    tags=["product", "listing", "price"],
    responses={
        200: "Product listing price deleted",
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
        provider.delete_price(
            id=request.id,
            sid=request.sid,
            date=request.date,
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
