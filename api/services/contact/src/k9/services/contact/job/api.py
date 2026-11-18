from k9.resolvers.http.errors import Forbidden, NotFound, TooManyRequests, Unauthorized
from k9.resolvers.http.responses import OK, Created, NoContent
from k9.types.common import Caller
from k9.types.errors import (
    DomainForbidden,
    DomainNotFound,
    DomainRateLimited,
    DomainUnauthorized,
)

from .. import app
from .http import Create, Delete, Update
from .provider import Job, JobProvider

provider = JobProvider()
app.grant(*provider.permissions)


@app.post(
    "/contacts/<id>/jobs/<date>",
    summary="Create job for contact",
    tags=["contact", "job"],
    responses={
        201: "Job created",
        401: "Authentication required",
        403: "Access denied",
        429: "Too many requests",
    },
)
def create(
    caller: Caller,
    request: Create,
) -> Created[Job] | Unauthorized | Forbidden | TooManyRequests:
    try:
        caller.require_admin()
        job = provider.create_job(
            id=request.id,
            date=request.date,
            scope=request.scope,
            company=request.company,
            title=request.title,
            email=request.email,
            phone=request.phone,
        )
        return Created(Job.model_validate(job))
    except DomainUnauthorized as exc:
        return Unauthorized(cause=exc)
    except DomainForbidden as exc:
        return Forbidden(cause=exc)
    except DomainRateLimited as exc:
        return TooManyRequests(cause=exc)


@app.patch(
    "/contacts/<id>/jobs/<date>",
    summary="Update job for contact",
    tags=["contact", "job"],
    responses={
        200: "Job updated",
        401: "Authentication required",
        403: "Access denied",
        404: "Job not found",
        429: "Too many requests",
    },
)
def update(
    caller: Caller,
    request: Update,
) -> OK[Job] | Unauthorized | Forbidden | NotFound | TooManyRequests:
    try:
        caller.require_admin()
        job = provider.update_job(
            id=request.id,
            date=request.date,
            scope=request.scope,
            company=request.company,
            title=request.title,
            email=request.email,
            phone=request.phone,
        )
        return OK(Job.model_validate(job))
    except DomainUnauthorized as exc:
        return Unauthorized(cause=exc)
    except DomainForbidden as exc:
        return Forbidden(cause=exc)
    except DomainNotFound as exc:
        return NotFound(cause=exc)
    except DomainRateLimited as exc:
        return TooManyRequests(cause=exc)


@app.delete(
    "/contacts/<id>/jobs/<date>",
    summary="Delete job for contact",
    tags=["contact", "job"],
    responses={
        200: "Job deleted",
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
        provider.delete_job(
            id=request.id,
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
