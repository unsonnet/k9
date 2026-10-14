from shared.helpers import load_apis
from shared.resolvers.http import HttpResolver

__all__ = [
    "app",
    "lambda_handler",
]

app = HttpResolver(enable_validation=True)
load_apis(__name__, __path__)


def lambda_handler(event, context):
    return app.resolve(event, context)
