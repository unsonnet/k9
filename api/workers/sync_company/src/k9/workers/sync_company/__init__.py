from k9.resolvers.base import load_apis
from k9.resolvers.s3 import S3Resolver

__all__ = [
    "app",
    "lambda_handler",
]

app = S3Resolver()
load_apis(__name__, __path__)


def lambda_handler(event, context):
    return app.resolve(event, context)
