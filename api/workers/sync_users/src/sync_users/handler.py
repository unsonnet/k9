from shared.s3 import S3Resolver

from .models import Sync
from .provider import SyncUserProvider

app = S3Resolver()
provider = SyncUserProvider()
app.grant(*provider.permissions)


def lambda_handler(event, context):
    return app.resolve(event, context)


# ──── Event Endpoints ─────────────────────────────────────────────────────────────────


@app.created("users/*/picture.jxl")
def sync_user(request: Sync.Resource) -> None:
    provider.sync_user(request.key, id=request.id)
