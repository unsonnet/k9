from k9.resolvers.dynamodb import DynamoDBResolver
from k9.shared.helpers import load_apis

__all__ = [
    "app",
    "lambda_handler",
]

app = DynamoDBResolver()
load_apis(__name__, __path__)


def lambda_handler(event, context):
    return app.resolve(event, context)
