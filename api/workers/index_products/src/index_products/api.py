from shared.errors import DomainNotFound

from . import app
from .models import Drop, Index
from .provider import IndexProductProvider

provider = IndexProductProvider()
app.grant(*provider.permissions)


@app.insert("product")
@app.modify("product")
def index_product(request: Index.Product) -> None:
    provider.index(
        type=request.type,
        id=request.id,
        brand=request.brand,
        material=request.material,
        format=request.format.model_dump(),
        **{"$subformat": [i.model_dump() for i in request.subformats]},
    )


@app.insert("product.image")
@app.modify("product.image")
def index_image(request: Index.Image) -> None:
    provider.index(
        type=request.type,
        id=request.id,
        url=request.url,
    )


@app.insert("product.listing")
@app.modify("product.listing")
def index_listing(request: Index.Listing) -> None:
    provider.index(
        type=request.type,
        id=request.id,
        vendor=request.vendor,
        sku=request.sku,
        name=request.name,
    )


@app.remove("product")
@app.remove("product.image")
@app.remove("product.listing")
def drop(request: Drop.Item) -> None:
    try:
        provider.drop(
            type=request.type,
            id=request.id,
        )
    except DomainNotFound:
        pass
