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
from .provider import CompanyContactProvider

app = HttpResolver(enable_validation=True)
provider = CompanyContactProvider()
app.grant(*provider.permissions)


@app.post(
    "/companies/<id>/contacts",
    summary="Create company contact",
    description="Create a contact of a company. Requires admin role.",
    tags=["company", "contact"],
    responses={
        201: "Company contact created",
        401: "Authentication required",
        403: "Access denied",
        429: "Too many requests",
    },
)
def create(
    caller: Caller,
    request: Request.Create,
) -> Created[Response.Contact] | Unauthorized | Forbidden | TooManyRequests:
    try:
        require_admin(caller)
        contact = provider.create_contact(
            id=request.id,
            sid=generate_subresource_id(),
            name=request.name,
            title=request.title,
            email=request.email,
            phone=request.phone,
        )
        return Created(Response.Contact.pack(contact))
    except DomainUnauthorized as exc:
        return Unauthorized(cause=exc)
    except DomainForbidden as exc:
        return Forbidden(cause=exc)
    except DomainRateLimited as exc:
        return TooManyRequests(cause=exc)


@app.get(
    "/companies/<id>/contacts/<sid>",
    summary="Read company contact",
    description="Read a contact of a company.",
    tags=["company", "contact"],
    responses={
        200: "Company contact found",
        401: "Authentication required",
        404: "Company contact not found",
        429: "Too many requests",
    },
)
def read(
    caller: Caller,
    request: Request.Read,
) -> OK[Response.Contact] | Unauthorized | NotFound | TooManyRequests:
    try:
        contact = provider.read_contact(
            id=request.id,
            sid=request.sid,
        )
        return OK(Response.Contact.pack(contact))
    except DomainUnauthorized as exc:
        return Unauthorized(cause=exc)
    except DomainNotFound as exc:
        return NotFound(cause=exc)
    except DomainRateLimited as exc:
        return TooManyRequests(cause=exc)


@app.patch(
    "/companies/<id>/contacts/<sid>",
    summary="Update company contact",
    description="Update a contact of a company. Requires admin role.",
    tags=["company", "contact"],
    responses={
        200: "Company contact updated",
        401: "Authentication required",
        403: "Access denied",
        404: "Company contact not found",
        429: "Too many requests",
    },
)
def update(
    caller: Caller,
    request: Request.Update,
) -> OK[Response.Contact] | Unauthorized | Forbidden | NotFound | TooManyRequests:
    try:
        require_admin(caller)
        contact = provider.update_contact(
            id=request.id,
            sid=request.sid,
            name=request.name,
            title=request.title,
            picture=request.picture,
            email=request.email,
            phone=request.phone,
        )
        return OK(Response.Contact.pack(contact))
    except DomainUnauthorized as exc:
        return Unauthorized(cause=exc)
    except DomainForbidden as exc:
        return Forbidden(cause=exc)
    except DomainNotFound as exc:
        return NotFound(cause=exc)
    except DomainRateLimited as exc:
        return TooManyRequests(cause=exc)


@app.delete(
    "/companies/<id>/contacts/<sid>",
    summary="Delete company contact",
    description="Delete a contact of a company. Requires admin role.",
    tags=["company", "contact"],
    responses={
        200: "Company contact deleted",
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
        provider.delete_contact(
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


@app.post(
    "/companies/<id>/contacts/<sid>/picture",
    summary="Upload company contact picture",
    description="Create a company contact picture upload form. Requires admin role.",
    tags=["company", "contact"],
    responses={
        200: "Company contact picture upload form created",
        401: "Authentication required",
        403: "Access denied",
        404: "Company not found",
        429: "Too many requests",
    },
)
def picture(
    caller: Caller,
    request: Request.Picture,
) -> OK[Response.UploadURL] | Unauthorized | Forbidden | NotFound | TooManyRequests:
    try:
        require_admin(caller)
        form = provider.upload_picture(
            id=request.id,
            sid=request.sid,
            content_type=request.contentType,
            max_bytes=5 * 1024 * 1024,
            max_seconds=5 * 60,
        )
        return OK(Response.UploadURL.pack(form))
    except DomainUnauthorized as exc:
        return Unauthorized(cause=exc)
    except DomainForbidden as exc:
        return Forbidden(cause=exc)
    except DomainNotFound as exc:
        return NotFound(cause=exc)
    except DomainRateLimited as exc:
        return TooManyRequests(cause=exc)


def lambda_handler(event, context):
    return app.resolve(event, context)
