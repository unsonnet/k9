import base64
import io
import json
from typing import Any, Dict, Optional


def make_event(path: str, method: str, *, headers: Optional[Dict[str, str]] = None, body: Optional[Any] = None, query: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "rawPath": path,
        "requestContext": {"http": {"method": method}},
    }
    if headers:
        payload["headers"] = headers
    if query:
        payload["queryStringParameters"] = query
    if body is not None:
        if isinstance(body, (dict, list)):
            payload["body"] = json.dumps(body)
        elif isinstance(body, (bytes, bytearray)):
            payload["body"] = body.decode("utf-8")
        else:
            payload["body"] = str(body)
    return payload


def png_base64(size: int = 2) -> str:
    try:
        from PIL import Image  # type: ignore
    except Exception as e:  # noqa: BLE001
        raise RuntimeError("Pillow is required for png_base64 helper") from e
    img = Image.new("RGB", (size, size), color=(255, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")
