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

from .models import Request, Response
from .provider import CompanyLocationProvider

app = HttpResolver(enable_validation=True)
provider = CompanyLocationProvider()
app.grant(*provider.permissions)


@app.post(
    "/companies/<id>/locations",
    summary="Create company location",
    description="Create a location of a company. Requires admin role.",
    tags=["company", "location"],
    responses={
        201: "Company location created",
        401: "Authentication required",
        403: "Access denied",
        429: "Too many requests",
    },
)
def create(
    caller: Caller,
    request: Request.Create,
) -> Created[Response.Location] | Unauthorized | Forbidden | TooManyRequests:
    try:
        require_admin(caller)
        location = provider.create_location(
            id=request.id,
            sid=generate_subresource_id(),
            street=request.street,
            city=request.city,
            state=request.state,
            zip=request.zip,
        )
        return Created(Response.Location.pack(location))
    except DomainUnauthorized as exc:
        return Unauthorized(cause=exc)
    except DomainForbidden as exc:
        return Forbidden(cause=exc)
    except DomainRateLimited as exc:
        return TooManyRequests(cause=exc)


@app.get(
    "/companies/<id>/locations/<sid>",
    summary="Read company location",
    description="Read a location of a company.",
    tags=["company", "location"],
    responses={
        200: "Company location found",
        401: "Authentication required",
        404: "Company location not found",
        429: "Too many requests",
    },
)
def read(
    caller: Caller,
    request: Request.Read,
) -> OK[Response.Location] | Unauthorized | NotFound | TooManyRequests:
    try:
        location = provider.read_location(
            id=request.id,
            sid=request.sid,
        )
        return OK(Response.Location.pack(location))
    except DomainUnauthorized as exc:
        return Unauthorized(cause=exc)
    except DomainNotFound as exc:
        return NotFound(cause=exc)
    except DomainRateLimited as exc:
        return TooManyRequests(cause=exc)


@app.delete(
    "/companies/<id>/locations/<sid>",
    summary="Delete company location",
    description="Delete a location of a company. Requires admin role.",
    tags=["company", "location"],
    responses={
        200: "Company location deleted",
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
        provider.delete_location(
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


def lambda_handler(event, context):
    return app.resolve(event, context)
