from k9.shared.errors import DomainNotFound

from . import app
from .models import Image, Listing, Product
from .provider import IndexProductProvider

provider = IndexProductProvider()
app.grant(*provider.permissions)


@app.insert("products")
@app.modify("products")
def index_product(key: str, new: Product) -> None:
    provider.index(
        key,
        id=new.id,
        brand=new.brand,
        material=new.material.model_dump(),
        format=new.format.model_dump(),
        **{"$subformats": [i.model_dump() for i in new.subformats]},
    )


@app.insert("products/images")
@app.modify("products/images")
def index_image(key: str, new: Image) -> None:
    provider.index(
        key,
        id=new.id,
        url=str(new.url),
    )


@app.insert("products/listings")
@app.modify("products/listings")
def index_listing(key: str, new: Listing) -> None:
    provider.index(
        key,
        id=new.id,
        vendor=new.vendor,
        sku=new.sku,
        name=new.name,
    )


@app.remove("products")
@app.remove("products/images")
@app.remove("products/listings")
def drop(key: str) -> None:
    try:
        provider.drop(key)
    except DomainNotFound:
        pass
