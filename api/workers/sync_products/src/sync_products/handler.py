from shared.resolvers.s3 import S3Resolver

from .models import Sync
from .provider import SyncProductProvider

app = S3Resolver()
provider = SyncProductProvider()
app.grant(*provider.permissions)


def lambda_handler(event, context):
    return app.resolve(event, context)


# ──── Event Endpoints ─────────────────────────────────────────────────────────────────


FORMATS = "{png,jpeg,jxl,heic,webp}"


@app.created(f"uploads/products/*/reference.{FORMATS}")
def sync_image(request: Sync.Subresource) -> None:
    provider.sync_image(request.key, id=request.id, sid=request.sid)
