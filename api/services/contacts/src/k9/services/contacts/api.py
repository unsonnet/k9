from k9.resolvers.http.errors import Forbidden, NotFound, TooManyRequests, Unauthorized
from k9.resolvers.http.responses import OK, Created, NoContent
from k9.shared.errors import (
    DomainForbidden,
    DomainNotFound,
    DomainRateLimited,
    DomainUnauthorized,
)
from k9.shared.helpers import require_admin
from k9.types.common import Caller, ResourceID

from . import app
from .http import Request, Response
from .provider import ContactProvider

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
    request: Request.Create,
) -> Created[Response.Contact] | Unauthorized | Forbidden | TooManyRequests:
    try:
        require_admin(caller)
        contact = provider.create_contact(
            id=ResourceID.random(),
            scope=request.scope,
            type=request.type,
            name=request.name,
            email=request.email,
            phone=request.phone,
        )
        return Created(Response.Contact.model_validate(contact))
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
    request: Request.Read,
) -> OK[Response.Contact] | Unauthorized | NotFound | TooManyRequests:
    try:
        contact = provider.read_contact(
            id=request.id,
        )
        return OK(Response.Contact.model_validate(contact))
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
    request: Request.Update,
) -> OK[Response.Contact] | Unauthorized | Forbidden | NotFound | TooManyRequests:
    try:
        require_admin(caller)
        contact = provider.update_contact(
            id=request.id,
            scope=request.scope,
            type=request.type,
            name=request.name,
            picture=request.picture,
            email=request.email,
            phone=request.phone,
        )
        return OK(Response.Contact.model_validate(contact))
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
    request: Request.Delete,
) -> NoContent | Unauthorized | Forbidden | TooManyRequests:
    try:
        require_admin(caller)
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
    request: Request.Picture,
) -> OK[Response.Upload] | Unauthorized | Forbidden | NotFound | TooManyRequests:
    try:
        require_admin(caller)
        form = provider.upload_picture(
            id=request.id,
            format=request.format,
            length=request.length,
        )
        return OK(Response.Upload.model_validate(form))
    except DomainUnauthorized as exc:
        return Unauthorized(cause=exc)
    except DomainForbidden as exc:
        return Forbidden(cause=exc)
    except DomainNotFound as exc:
        return NotFound(cause=exc)
    except DomainRateLimited as exc:
        return TooManyRequests(cause=exc)
