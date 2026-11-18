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
from .provider import Contact, ContactProvider, UploadForm

provider = ContactProvider()
app.grant(*provider.permissions)


@app.post(
    "/contacts",
    summary="Create contact",
    tags=["contact"],
    responses={
        201: "Contact created",
        401: "Authentication required",
        403: "Access denied",
        429: "Too many requests",
    },
)
def create(
    caller: Caller,
    request: Create,
) -> Created[Contact] | Unauthorized | Forbidden | TooManyRequests:
    try:
        caller.require_admin()
        contact = provider.create_contact(
            id=ResourceID.random(),
            scope=request.scope,
            type=request.type,
            name=request.name,
            email=request.email,
            phone=request.phone,
        )
        return Created(contact)
    except DomainUnauthorized as exc:
        return Unauthorized(cause=exc)
    except DomainForbidden as exc:
        return Forbidden(cause=exc)
    except DomainRateLimited as exc:
        return TooManyRequests(cause=exc)


@app.get(
    "/contacts/<id>",
    summary="Read contact",
    tags=["contact"],
    responses={
        200: "Contact found",
        401: "Authentication required",
        404: "Contact not found",
        429: "Too many requests",
    },
)
def read(
    caller: Caller,
    request: Read,
) -> OK[Contact] | Unauthorized | NotFound | TooManyRequests:
    try:
        contact = provider.read_contact(
            id=request.id,
        )
        return OK(contact)
    except DomainUnauthorized as exc:
        return Unauthorized(cause=exc)
    except DomainNotFound as exc:
        return NotFound(cause=exc)
    except DomainRateLimited as exc:
        return TooManyRequests(cause=exc)


@app.patch(
    "/contacts/<id>",
    summary="Update contact",
    tags=["contact"],
    responses={
        200: "Contact updated",
        401: "Authentication required",
        403: "Access denied",
        404: "Contact not found",
        429: "Too many requests",
    },
)
def update(
    caller: Caller,
    request: Update,
) -> OK[Contact] | Unauthorized | Forbidden | NotFound | TooManyRequests:
    try:
        caller.require_admin()
        contact = provider.update_contact(
            id=request.id,
            scope=request.scope,
            type=request.type,
            name=request.name,
            picture=request.picture,
            email=request.email,
            phone=request.phone,
        )
        return OK(contact)
    except DomainUnauthorized as exc:
        return Unauthorized(cause=exc)
    except DomainForbidden as exc:
        return Forbidden(cause=exc)
    except DomainNotFound as exc:
        return NotFound(cause=exc)
    except DomainRateLimited as exc:
        return TooManyRequests(cause=exc)


@app.delete(
    "/contacts/<id>",
    summary="Delete contact",
    tags=["contact"],
    responses={
        200: "Contact deleted",
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
        provider.delete_contact(
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
    "/contacts/<id>/picture",
    summary="Upload contact picture",
    tags=["contact"],
    responses={
        200: "Contact picture upload form created",
        401: "Authentication required",
        403: "Access denied",
        404: "Contact not found",
        429: "Too many requests",
    },
)
def upload(
    caller: Caller,
    request: Upload,
) -> OK[UploadForm] | Unauthorized | Forbidden | NotFound | TooManyRequests:
    try:
        caller.require_admin()
        form = provider.upload_picture(
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
