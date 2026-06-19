from shared.errors import (
    DomainForbidden,
    DomainNotFound,
    DomainRateLimited,
    DomainUnauthorized,
)
from shared.helpers import require_admin
from shared.http import Caller, HttpResolver
from shared.http.errors import Forbidden, NotFound, TooManyRequests, Unauthorized
from shared.http.responses import OK, Created, NoContent
from shared.provider.company import generate_id

from .models import Request, Response
from .provider import CompanyProvider, DynamoDBCompanyProvider

app = HttpResolver(strip_prefixes=["/company"], enable_validation=True)
provider: CompanyProvider = DynamoDBCompanyProvider()
app.grant(*provider.permissions)


@app.get(
    "/",
    summary="List companies",
    description="List or search companies.",
    tags=["company"],
    responses={
        200: "Companies found",
        401: "Authentication required",
        403: "Access denied",
        429: "Too many requests",
    },
)
def list(
    caller: Caller,
    request: Request.List,
) -> OK[Response.Page] | Unauthorized | TooManyRequests:
    try:
        page = provider.list_companies(
            q=request.q,
            g=(request.lat, request.lon, request.radius)
            if (
                request.lat is not None
                and request.lon is not None
                and request.radius is not None
            )
            else None,
            limit=request.limit or 25,
            cursor=request.cursor,
        )
        return OK(Response.Page.pack(page))
    except DomainUnauthorized as exc:
        return Unauthorized(cause=exc)
    except DomainRateLimited as exc:
        return TooManyRequests(cause=exc)


@app.post(
    "/",
    summary="Create company profile",
    description="Create a new company profile. Requires admin role.",
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
    request: Request.Create,
) -> Created[Response.Company] | Unauthorized | Forbidden | TooManyRequests:
    try:
        require_admin(caller)
        company = provider.create_company(
            id=generate_id(),
            sector=request.sector,
            name=request.name,
            website=request.website,
            locations=request.locations,
            contacts=request.contacts,
        )
        return Created(Response.Company.pack(company))
    except DomainUnauthorized as exc:
        return Unauthorized(cause=exc)
    except DomainForbidden as exc:
        return Forbidden(cause=exc)
    except DomainRateLimited as exc:
        return TooManyRequests(cause=exc)


@app.get(
    "/<id>",
    summary="Read company profile",
    description="Read a company profile.",
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
    request: Request.Read,
) -> OK[Response.Company] | Unauthorized | NotFound | TooManyRequests:
    try:
        company = provider.read_company(
            id=request.id,
        )
        return OK(Response.Company.pack(company))
    except DomainUnauthorized as exc:
        return Unauthorized(cause=exc)
    except DomainNotFound as exc:
        return NotFound(cause=exc)
    except DomainRateLimited as exc:
        return TooManyRequests(cause=exc)


@app.patch(
    "/<id>",
    summary="Update company profile",
    description="Update a company profile. Requires admin role.",
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
    request: Request.Update,
) -> OK[Response.Company] | Unauthorized | Forbidden | NotFound | TooManyRequests:
    try:
        require_admin(caller)
        company = provider.update_company(
            id=request.id,
            sector=request.sector,
            name=request.name,
            website=request.website,
            locations=request.locations,
            contacts=request.contacts,
        )
        return OK(Response.Company.pack(company))
    except DomainUnauthorized as exc:
        return Unauthorized(cause=exc)
    except DomainForbidden as exc:
        return Forbidden(cause=exc)
    except DomainNotFound as exc:
        return NotFound(cause=exc)
    except DomainRateLimited as exc:
        return TooManyRequests(cause=exc)


@app.delete(
    "/<id>",
    summary="Delete company profile",
    description="Delete a company profile. Requires admin role.",
    tags=["company"],
    responses={
        204: "Company deleted",
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
    "/<id>/logo",
    summary="Create company logo upload form",
    description="Create a company logo upload form. Requires admin role.",
    tags=["company"],
    responses={
        200: "Company logo upload form created",
        401: "Authentication required",
        403: "Access denied",
        404: "Company not found",
        429: "Too many requests",
    },
)
def logo(
    caller: Caller,
    request: Request.Logo,
) -> OK[Response.UploadForm] | Unauthorized | Forbidden | NotFound | TooManyRequests:
    try:
        require_admin(caller)
        form = provider.generate_upload_form(
            id=request.id,
            content_type=request.contentType,
            max_bytes=5 * 1024 * 1024,
            max_seconds=5 * 60,
        )
        return OK(Response.UploadForm.pack(form))
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
