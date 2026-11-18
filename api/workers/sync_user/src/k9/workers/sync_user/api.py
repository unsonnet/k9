from . import app
from .models import Resource
from .provider import SyncUserProvider

provider = SyncUserProvider()
app.grant(*provider.permissions)

FORMATS = "{png,jpeg,jxl,heic,webp}"


@app.created(f"uploads/users/*/picture.{FORMATS}")
def update_picture(request: Resource) -> None:
    provider.update_picture(request.key, id=request.id)
