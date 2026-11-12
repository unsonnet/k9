from . import app
from .models import Resource
from .provider import SyncCompanyProvider

provider = SyncCompanyProvider()
app.grant(*provider.permissions)

FORMATS = "{png,jpeg,jxl,heic,webp}"


@app.created(f"uploads/companies/*/logo.{FORMATS}")
def sync_company(request: Resource) -> None:
    provider.sync_company(request.key, id=request.id)
