from . import app
from .models import Resource
from .provider import SyncUserProvider

provider = SyncUserProvider()
app.grant(*provider.permissions)

FORMATS = "{png,jpeg,jxl,heic,webp}"


@app.created(f"uploads/users/*/picture.{FORMATS}")
def sync_user(request: Resource) -> None:
    provider.sync_user(request.key, id=request.id)
