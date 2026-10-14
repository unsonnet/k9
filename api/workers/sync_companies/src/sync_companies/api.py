from . import app
from .models import Sync
from .provider import SyncCompanyProvider

provider = SyncCompanyProvider()
app.grant(*provider.permissions)

FORMATS = "{png,jpeg,jxl,heic,webp}"


@app.created(f"uploads/companies/*/logo.{FORMATS}")
def sync_company(request: Sync.Resource) -> None:
    provider.sync_company(request.key, id=request.id)


@app.created(f"uploads/companies/*/picture.{FORMATS}")
def sync_contact(request: Sync.Subresource) -> None:
    provider.sync_contact(request.key, id=request.id, sid=request.sid)
