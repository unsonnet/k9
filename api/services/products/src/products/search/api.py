from shared.errors import DomainNotFound, DomainRateLimited, DomainUnauthorized
from shared.resolvers.http import Caller
from shared.resolvers.http.errors import NotFound, TooManyRequests, Unauthorized
from shared.resolvers.http.responses import OK

from .. import app
from .http import Request, Response
from .provider import ProductSearchProvider

provider = ProductSearchProvider()
app.grant(*provider.permissions)


@app.post(
    "/products/search",
    summary="Search products",
    description="Search products by name, sku, brand, vendor, material, and format.",
    tags=["product", "search"],
    responses={
        200: "Products found",
        401: "Authentication required",
        404: "Reference product not found",
        429: "Too many requests",
    },
)
def search(
    caller: Caller,
    request: Request.Search,
) -> OK[Response.Page] | Unauthorized | NotFound | TooManyRequests:
    try:
        page = provider.search_products(
            q=request.q,
            sku=request.sku,
            store=request.store,
            material=request.material,
            format=request.format,
            reference=request.reference,
            limit=request.limit,
            cursor=request.cursor,
        )
        return OK(Response.Page.model_validate(page))
    except DomainUnauthorized as exc:
        return Unauthorized(cause=exc)
    except DomainNotFound as exc:
        return NotFound(cause=exc)
    except DomainRateLimited as exc:
        return TooManyRequests(cause=exc)
