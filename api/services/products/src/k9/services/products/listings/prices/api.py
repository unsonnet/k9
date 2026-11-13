from k9.resolvers.http.errors import Forbidden, NotFound, TooManyRequests, Unauthorized
from k9.resolvers.http.responses import OK, Created, NoContent
from k9.shared.errors import (
    DomainForbidden,
    DomainNotFound,
    DomainRateLimited,
    DomainUnauthorized,
)
from k9.shared.helpers import require_admin
from k9.types.common import Caller

from ... import app
from .http import Request, Response
from .provider import PriceProvider

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
    request: Request.Create,
) -> Created[Response.Price] | Unauthorized | Forbidden | TooManyRequests:
    try:
        require_admin(caller)
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
        return Created(Response.Price.model_validate(price))
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
    request: Request.Update,
) -> OK[Response.Price] | Unauthorized | Forbidden | NotFound | TooManyRequests:
    try:
        require_admin(caller)
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
        return OK(Response.Price.model_validate(price))
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
    request: Request.Delete,
) -> NoContent | Unauthorized | Forbidden | TooManyRequests:
    try:
        require_admin(caller)
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
