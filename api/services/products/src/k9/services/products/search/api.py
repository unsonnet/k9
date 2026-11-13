from k9.resolvers.http.errors import (
    MethodNotImplemented,
    NotFound,
    TooManyRequests,
    Unauthorized,
)
from k9.resolvers.http.responses import OK
from k9.shared.errors import DomainNotFound, DomainRateLimited, DomainUnauthorized
from k9.types.common import Caller

from .. import app
from .http import Request, Response
from .provider import ProductSearchProvider

provider = ProductSearchProvider()
app.grant(*provider.permissions)


@app.post(
    "/products/search",
    summary="Search products",
    description="Search products by name, sku, store, material, and format.",
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
) -> (
    OK[Response.Page] | Unauthorized | NotFound | TooManyRequests | MethodNotImplemented
):
    try:
        return MethodNotImplemented("Product search is not implemented")
    except DomainUnauthorized as exc:
        return Unauthorized(cause=exc)
    except DomainNotFound as exc:
        return NotFound(cause=exc)
    except DomainRateLimited as exc:
        return TooManyRequests(cause=exc)
