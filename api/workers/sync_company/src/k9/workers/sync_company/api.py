from . import app
from .models import Resource
from .provider import SyncCompanyProvider

provider = SyncCompanyProvider()
app.grant(*provider.permissions)

FORMATS = "{png,jpeg,jxl,heic,webp}"


@app.created(f"uploads/companies/*/logo.{FORMATS}")
def update_logo(request: Resource) -> None:
    provider.update_logo(request.key, id=request.id)
