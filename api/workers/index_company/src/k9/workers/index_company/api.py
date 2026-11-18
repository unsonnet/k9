from k9.types.company import Company, Location
from k9.types.errors import DomainNotFound

from . import app
from .provider import IndexCompanyProvider

provider = IndexCompanyProvider()
app.grant(*provider.permissions)


@app.insert("companies")
@app.modify("companies")
def index_company(key: str, new: Company) -> None:
    provider.index(
        key,
        id=new.id,
        type=new.type,
        name=new.name,
        logo=str(new.logo),
        website=str(new.website) if new.website else None,
    )


@app.insert("companies/locations")
@app.modify("companies/locations")
def index_location(key: str, new: Location) -> None:
    provider.index(
        key,
        id=new.id,
        geo={"lat": float(new.geo.lat), "lon": float(new.geo.lng)},
    )


@app.remove("companies")
@app.remove("companies/locations")
def drop(key: str) -> None:
    try:
        provider.drop(key)
    except DomainNotFound:
        pass
