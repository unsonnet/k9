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
from .provider import Location, LocationProvider

provider = LocationProvider()
app.grant(*provider.permissions)


@app.post(
    "/companies/<id>/locations",
    summary="Create company location",
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
    request: Create,
) -> Created[Location] | Unauthorized | Forbidden | TooManyRequests:
    try:
        caller.require_admin()
        location = provider.create_location(
            id=request.id,
            sid=SubresourceID.random(),
            scope=request.scope,
            street=request.street,
            city=request.city,
            state=request.state,
            zip=request.zip,
        )
        return Created(location)
    except DomainUnauthorized as exc:
        return Unauthorized(cause=exc)
    except (DomainForbidden, AssertionError) as exc:
        return Forbidden(cause=exc)
    except DomainRateLimited as exc:
        return TooManyRequests(cause=exc)


@app.patch(
    "/companies/<id>/locations/<sid>",
    summary="Update company location",
    tags=["company", "location"],
    responses={
        200: "Company location updated",
        401: "Authentication required",
        403: "Access denied",
        404: "Company location not found",
        429: "Too many requests",
    },
)
def update(
    caller: Caller,
    request: Update,
) -> OK[Location] | Unauthorized | Forbidden | NotFound | TooManyRequests:
    try:
        caller.require_admin()
        location = provider.update_location(
            id=request.id,
            sid=request.sid,
            scope=request.scope,
        )
        return OK(location)
    except DomainUnauthorized as exc:
        return Unauthorized(cause=exc)
    except DomainForbidden as exc:
        return Forbidden(cause=exc)
    except DomainNotFound as exc:
        return NotFound(cause=exc)
    except DomainRateLimited as exc:
        return TooManyRequests(cause=exc)


@app.delete(
    "/companies/<id>/locations/<sid>",
    summary="Delete company location",
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
    request: Delete,
) -> NoContent | Unauthorized | Forbidden | TooManyRequests:
    try:
        caller.require_admin()
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
