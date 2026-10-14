from shared.helpers import load_apis
from shared.resolvers.s3 import S3Resolver

__all__ = [
    "app",
    "lambda_handler",
]

app = S3Resolver()
load_apis(__name__, __path__)


def lambda_handler(event, context):
    return app.resolve(event, context)
