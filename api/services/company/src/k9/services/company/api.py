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
from .http import Create, Delete, Read, Update, Upload
from .provider import Company, CompanyProvider, UploadForm

provider = CompanyProvider()
app.grant(*provider.permissions)


@app.post(
    "/companies",
    summary="Create company",
    tags=["company"],
    responses={
        201: "Company created",
        401: "Authentication required",
        403: "Access denied",
        429: "Too many requests",
    },
)
def create(
    caller: Caller,
    request: Create,
) -> Created[Company] | Unauthorized | Forbidden | TooManyRequests:
    try:
        caller.require_admin()
        company = provider.create_company(
            id=ResourceID.random(),
            scope=request.scope,
            type=request.type,
            name=request.name,
            website=request.website,
        )
        return Created(company)
    except DomainUnauthorized as exc:
        return Unauthorized(cause=exc)
    except DomainForbidden as exc:
        return Forbidden(cause=exc)
    except DomainRateLimited as exc:
        return TooManyRequests(cause=exc)


@app.get(
    "/companies/<id>",
    summary="Read company",
    tags=["company"],
    responses={
        200: "Company found",
        401: "Authentication required",
        404: "Company not found",
        429: "Too many requests",
    },
)
def read(
    caller: Caller,
    request: Read,
) -> OK[Company] | Unauthorized | NotFound | TooManyRequests:
    try:
        company = provider.read_company(
            id=request.id,
        )
        return OK(company)
    except DomainUnauthorized as exc:
        return Unauthorized(cause=exc)
    except DomainNotFound as exc:
        return NotFound(cause=exc)
    except DomainRateLimited as exc:
        return TooManyRequests(cause=exc)


@app.patch(
    "/companies/<id>",
    summary="Update company",
    tags=["company"],
    responses={
        200: "Company updated",
        401: "Authentication required",
        403: "Access denied",
        404: "Company not found",
        429: "Too many requests",
    },
)
def update(
    caller: Caller,
    request: Update,
) -> OK[Company] | Unauthorized | Forbidden | NotFound | TooManyRequests:
    try:
        caller.require_admin()
        company = provider.update_company(
            id=request.id,
            scope=request.scope,
            type=request.type,
            name=request.name,
            logo=request.logo,
            website=request.website,
        )
        return OK(company)
    except DomainUnauthorized as exc:
        return Unauthorized(cause=exc)
    except DomainForbidden as exc:
        return Forbidden(cause=exc)
    except DomainNotFound as exc:
        return NotFound(cause=exc)
    except DomainRateLimited as exc:
        return TooManyRequests(cause=exc)


@app.delete(
    "/companies/<id>",
    summary="Delete company",
    tags=["company"],
    responses={
        200: "Company deleted",
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
        provider.delete_company(
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


@app.post(
    "/companies/<id>/logo",
    summary="Upload company logo",
    tags=["company"],
    responses={
        200: "Company logo upload form created",
        401: "Authentication required",
        403: "Access denied",
        404: "Company not found",
        429: "Too many requests",
    },
)
def upload(
    caller: Caller,
    request: Upload,
) -> OK[UploadForm] | Unauthorized | Forbidden | NotFound | TooManyRequests:
    try:
        caller.require_admin()
        form = provider.upload_logo(
            id=request.id,
            format=request.format,
            length=request.length,
        )
        return OK(form)
    except DomainUnauthorized as exc:
        return Unauthorized(cause=exc)
    except DomainForbidden as exc:
        return Forbidden(cause=exc)
    except DomainNotFound as exc:
        return NotFound(cause=exc)
    except DomainRateLimited as exc:
        return TooManyRequests(cause=exc)
