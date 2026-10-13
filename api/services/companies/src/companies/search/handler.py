from shared.errors import DomainRateLimited, DomainUnauthorized
from shared.resolvers.http import Caller, HttpResolver
from shared.resolvers.http.errors import TooManyRequests, Unauthorized
from shared.resolvers.http.responses import OK

from .http import Request, Response
from .provider import CompanySearchProvider

__all__ = [
    "app",
    "lambda_handler",
]


app = HttpResolver(enable_validation=True)
provider = CompanySearchProvider()
app.grant(*provider.permissions)


def lambda_handler(event, context):
    return app.resolve(event, context)


# ──── API Endpoints ───────────────────────────────────────────────────────────────────


@app.get(
    "/companies/search",
    summary="Search companies",
    description="Search companies by sector, name, and coordinates.",
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
) -> OK[Response.Page] | Unauthorized | TooManyRequests:
    try:
        page = provider.search_companies(
            sector=request.sector,
            name=request.name,
            geo=request.geo,
            limit=request.limit,
            cursor=request.cursor,
        )
        return OK(Response.Page.model_validate(page))
    except DomainUnauthorized as exc:
        return Unauthorized(cause=exc)
    except DomainRateLimited as exc:
        return TooManyRequests(cause=exc)
