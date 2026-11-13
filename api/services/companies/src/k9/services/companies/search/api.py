from k9.resolvers.http.errors import MethodNotImplemented, TooManyRequests, Unauthorized
from k9.resolvers.http.responses import OK
from k9.shared.errors import DomainRateLimited, DomainUnauthorized
from k9.types.common import Caller

from .. import app
from .http import Request, Response
from .provider import CompanySearchProvider

provider = CompanySearchProvider()
app.grant(*provider.permissions)


@app.get(
    "/companies/search",
    summary="Search companies",
    description="Search companies by type, name, and coordinates.",
    tags=["company", "search"],
    responses={
        200: "Companies found",
        401: "Authentication required",
        429: "Too many requests",
    },
)
def search(
    caller: Caller,
    request: Request.Search,
) -> OK[Response.Page] | Unauthorized | TooManyRequests | MethodNotImplemented:
    try:
        return MethodNotImplemented("Company search is not implemented")
    except DomainUnauthorized as exc:
        return Unauthorized(cause=exc)
    except DomainRateLimited as exc:
        return TooManyRequests(cause=exc)
