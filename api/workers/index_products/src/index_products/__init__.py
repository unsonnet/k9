from shared.helpers import load_apis
from shared.resolvers.dynamodb import DynamoDBResolver

__all__ = [
    "app",
    "lambda_handler",
]

app = DynamoDBResolver()
load_apis(__name__, __path__)


def lambda_handler(event, context):
    return app.resolve(event, context)
