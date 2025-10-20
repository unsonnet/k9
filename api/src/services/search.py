from __future__ import annotations

from typing import Any, Dict, List, Optional

try:
    from opensearchpy import OpenSearch  # type: ignore
except Exception:  # noqa: BLE001
    OpenSearch = None  # type: ignore

from config import settings


class SearchService:
    def __init__(self) -> None:
        endpoint = settings().opensearch_endpoint
        if not endpoint:
            # Allow running without search (e.g., tests); operations will raise.
            self._client = None
        else:
            if OpenSearch is None:
                self._client = None
            else:
                self._client = OpenSearch(hosts=[{"host": endpoint, "port": 443, "scheme": "https"}])
        self._index = settings().opensearch_index

    def search(self, query: Dict[str, Any], from_: int, size: int) -> Dict[str, Any]:
        if not self._client:
            return {"hits": {"total": {"value": 0}, "hits": []}}
        body = dict(query)
        body.setdefault("from", from_)
        body.setdefault("size", size)
        return self._client.search(index=self._index, body=body)
