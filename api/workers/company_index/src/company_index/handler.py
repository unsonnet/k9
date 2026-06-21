from shared.errors import DomainNotFound
from shared.stream import DynamoDBStreamResolver

from .models import Request
from .provider import IndexProvider, OpenSearchIndexProvider

app = DynamoDBStreamResolver()
provider: IndexProvider = OpenSearchIndexProvider()
app.grant(*provider.permissions)


@app.insert
@app.modify
def index(request: Request.Upsert) -> None:
    company = request.company
    provider.index_company(
        id=company.id,
        sector=company.sector,
        name=company.name,
        logo=company.logo,
        website=company.website,
        locations=company.locations,
    )


@app.remove
def unindex(request: Request.Remove) -> None:
    try:
        provider.unindex_company(id=request.id)
    except DomainNotFound:
        pass  # already unindexed


def lambda_handler(event, context):
    return app.resolve(event, context)
