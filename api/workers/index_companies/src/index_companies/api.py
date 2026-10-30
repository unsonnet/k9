from shared.errors import DomainNotFound

from . import app
from .models import Drop, Index
from .provider import IndexCompanyProvider

provider = IndexCompanyProvider()
app.grant(*provider.permissions)


@app.insert("companies")
@app.modify("companies")
def index_company(request: Index.Company) -> None:
    provider.index(
        request.key["key"],
        id=request.id,
        type=request.type.value,
        name=request.name,
        logo=request.logo,
        website=request.website,
    )


@app.insert("companies/contacts")
@app.modify("companies/contacts")
def index_contact(request: Index.Contact) -> None:
    provider.index(
        request.key["key"],
        id=request.id,
        name=request.name,
        title=request.title,
        picture=request.picture,
        email=request.email,
        phone=request.phone,
    )


@app.insert("companies/locations")
@app.modify("companies/locations")
def index_location(request: Index.Location) -> None:
    provider.index(
        request.key["key"],
        id=request.id,
        street=request.street,
        city=request.city,
        state=request.state,
        zip=request.zip,
        geo={"lat": float(request.lat), "lon": float(request.lon)},
    )


@app.remove("companies")
@app.remove("companies/contacts")
@app.remove("companies/locations")
def drop(request: Drop.Item) -> None:
    try:
        provider.drop(request.key["key"])
    except DomainNotFound:
        pass
