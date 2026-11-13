from k9.resolvers.http import HttpResolver
from k9.shared.helpers import load_apis

__all__ = [
    "app",
    "lambda_handler",
]

app = HttpResolver(enable_validation=True)
load_apis(__name__, __path__)


def lambda_handler(event, context):
    return app.resolve(event, context)
