from shared.errors import DomainNotFound
from shared.resolvers.dynamodb import DynamoDBResolver

from .models import Remove, Sync
from .provider import CompanyIndexProvider

app = DynamoDBResolver()
provider = CompanyIndexProvider()
app.grant(*provider.permissions)


@app.insert("company")
@app.modify("company")
def sync_company(request: Sync.Company) -> None:
    provider.sync(
        type=request.type,
        id=request.id,
        sector=request.sector.value,
        name=request.name,
        logo=request.logo,
        website=request.website,
    )


@app.insert("company.contact")
@app.modify("company.contact")
def sync_contact(request: Sync.Contact) -> None:
    provider.sync(
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
def sync_location(request: Sync.Location) -> None:
    provider.sync(
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
def remove(request: Remove.Item) -> None:
    try:
        provider.remove(
            type=request.type,
            id=request.id,
        )
    except DomainNotFound:
        pass


def lambda_handler(event, context):
    return app.resolve(event, context)
