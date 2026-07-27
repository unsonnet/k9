from shared.errors import DomainNotFound
from shared.stream import DynamoDBStreamResolver

from .models import Request
from .provider import CompanyIndexProvider, CompanyItem, ContactItem, LocationItem

app = DynamoDBStreamResolver()
provider = CompanyIndexProvider()
app.grant(*provider.permissions)


@app.insert
@app.modify
def sync(request: Request.Upsert) -> None:
    match request.item:
        case CompanyItem():
            provider.sync_company(item=request.item)
        case ContactItem():
            provider.sync_contact(item=request.item)
        case LocationItem():
            provider.sync_location(item=request.item)


@app.remove
def remove(request: Request.Remove) -> None:
    try:
        match request.item:
            case CompanyItem():
                provider.delete_company(item=request.item)
            case ContactItem():
                provider.delete_contact(item=request.item)
            case LocationItem():
                provider.delete_location(item=request.item)
    except DomainNotFound:
        pass


def lambda_handler(event, context):
    return app.resolve(event, context)
