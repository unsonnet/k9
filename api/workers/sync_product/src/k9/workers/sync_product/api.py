from . import app
from .models import Subresource
from .provider import SyncProductProvider

provider = SyncProductProvider()
app.grant(*provider.permissions)

FORMATS = "{png,jpeg,jxl,heic,webp}"


@app.created(f"uploads/products/*/create.{FORMATS}")
def create_image(request: Subresource) -> None:
    provider.create_image(request.key, id=request.id, sid=request.sid)


@app.created(f"uploads/products/*/update.{FORMATS}")
def update_image(request: Subresource) -> None:
    provider.update_image(request.key, id=request.id, sid=request.sid)
