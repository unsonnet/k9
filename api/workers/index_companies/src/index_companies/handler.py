from shared.dynamodb import DynamoDBResolver
from shared.errors import DomainNotFound

from .models import Drop, Index
from .provider import IndexCompanyProvider

app = DynamoDBResolver()
provider = IndexCompanyProvider()
app.grant(*provider.permissions)


def lambda_handler(event, context):
    return app.resolve(event, context)


# ──── Event Endpoints ─────────────────────────────────────────────────────────────────


@app.insert("company")
@app.modify("company")
def index_company(request: Index.Company) -> None:
    provider.index(
        type=request.type,
        id=request.id,
        sector=request.sector.value,
        name=request.name,
        logo=request.logo,
        website=request.website,
    )


@app.insert("company.contact")
@app.modify("company.contact")
def index_contact(request: Index.Contact) -> None:
    provider.index(
        type=request.type,
        id=request.id,
        name=request.name,
        title=request.title,
        picture=request.picture,
        email=request.email,
        phone=request.phone,
    )


@app.insert("company.location")
@app.modify("company.location")
def index_location(request: Index.Location) -> None:
    provider.index(
        type=request.type,
        id=request.id,
        street=request.street,
        city=request.city,
        state=request.state,
        zip=request.zip,
        geo={"lat": float(request.lat), "lon": float(request.lon)},
    )


@app.remove("company")
@app.remove("company.contact")
@app.remove("company.location")
def drop(request: Drop.Item) -> None:
    try:
        provider.drop(
            type=request.type,
            id=request.id,
        )
    except DomainNotFound:
        pass
