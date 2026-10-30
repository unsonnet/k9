from shared.errors import DomainNotFound

from . import app
from .models import Drop, Index
from .provider import IndexProductProvider

provider = IndexProductProvider()
app.grant(*provider.permissions)


@app.insert("products")
@app.modify("products")
def index_product(request: Index.Product) -> None:
    provider.index(
        key=request.key["key"],
        id=request.id,
        brand=request.brand,
        material=request.material,
        format=request.format.model_dump(),
        **{"$subformat": [i.model_dump() for i in request.subformats]},
    )


@app.insert("products/images")
@app.modify("products/images")
def index_image(request: Index.Image) -> None:
    provider.index(
        key=request.key["key"],
        id=request.id,
        url=request.url,
    )


@app.insert("products/listings")
@app.modify("products/listings")
def index_listing(request: Index.Listing) -> None:
    provider.index(
        key=request.key["key"],
        id=request.id,
        vendor=request.vendor,
        sku=request.sku,
        name=request.name,
    )


@app.remove("products")
@app.remove("products/images")
@app.remove("products/listings")
def drop(request: Drop.Item) -> None:
    try:
        provider.drop(key=request.key["key"])
    except DomainNotFound:
        pass
