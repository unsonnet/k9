from __future__ import annotations

from typing import Any, Callable


def call_handler(handler_module: str, event: dict[str, Any]) -> dict[str, Any]:
    """
    Generic handler invoker to avoid duplication across test modules.
    Example: call_handler("auth", event)
    """
    module = __import__(f"src.handlers.{handler_module}", fromlist=["lambda_handler"])
    return module.lambda_handler(event, None)
