from k9.resolvers.base import load_apis
from k9.resolvers.dynamodb import DynamoDBResolver

__all__ = [
    "app",
    "lambda_handler",
]

app = DynamoDBResolver()
load_apis(__name__, __path__)


def lambda_handler(event, context):
    return app.resolve(event, context)
