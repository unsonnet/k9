from __future__ import annotations

import pytest


@pytest.fixture()
def auth_headers() -> dict[str, str]:
    """Minimal auth header fixture used by handlers that require Authorization."""
    return {"Authorization": "Bearer test-token-1234567890"}
