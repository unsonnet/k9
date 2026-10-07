from shared.s3 import S3Resolver

from .models import Sync
from .provider import SyncCompanyProvider

app = S3Resolver()
provider = SyncCompanyProvider()
app.grant(*provider.permissions)


def lambda_handler(event, context):
    return app.resolve(event, context)


# ──── Event Endpoints ─────────────────────────────────────────────────────────────────


FORMATS = "{png,jpeg,jxl,heic,webp}"


@app.created(f"uploads/companies/*/logo.{FORMATS}")
def sync_company(request: Sync.Resource) -> None:
    provider.sync_company(request.key, id=request.id)


@app.created(f"uploads/companies/*/picture.{FORMATS}")
def sync_contact(request: Sync.Subresource) -> None:
    provider.sync_contact(request.key, id=request.id, sid=request.sid)
