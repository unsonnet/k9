from __future__ import annotations

import json
from typing import Any, Dict, List

from models.api import SearchRequest
from services.search import SearchService
from utils.auth import parse_bearer, verify_token
from utils.http import InvalidRequest, response


svc = SearchService()


def _build_query(filters: SearchRequest, partial: bool) -> Dict[str, Any]:
    must: List[Dict[str, Any]] = []
    should: List[Dict[str, Any]] = []

    if filters.name:
        for field, value in filters.name.model_dump(exclude_none=True).items():
            must.append({"match": {f"name.{field}": {"query": value, "fuzziness": "AUTO"}}})

    if filters.category:
        for k, values in filters.category.items():
            must.append({"terms": {f"category.{k}": values}})

    if filters.format:
        fmt = filters.format
        if fmt.aspect:
            must.append({"term": {"formats.aspect": fmt.aspect}})
        for dim in ("length", "width", "thickness"):
            dr = getattr(fmt, dim)
            if dr and (dr.min is not None or dr.max is not None):
                rng: Dict[str, Any] = {}
                if dr.min is not None:
                    rng["gte"] = dr.min
                if dr.max is not None:
                    rng["lte"] = dr.max
                must.append({"range": {f"formats.{dim}.value": rng}})

    if filters.vendor:
        ven = filters.vendor
        if ven.store:
            must.append({"terms": {"formats.vendors.store": ven.store}})
        if ven.sku:
            must.append({"match": {"formats.vendors.sku": {"query": ven.sku, "fuzziness": "AUTO"}}})
        if ven.name:
            must.append({"match": {"formats.vendors.name": {"query": ven.name, "fuzziness": "AUTO"}}})
        if ven.discontinued is not None:
            must.append({"term": {"formats.vendors.discontinued": ven.discontinued}})
        if ven.price:
            pr = ven.price
            rng: Dict[str, Any] = {}
            if pr.min is not None:
                rng["gte"] = pr.min
            if pr.max is not None:
                rng["lte"] = pr.max
            must.append({"range": {"formats.vendors.price.value": rng}})

    # Vector/similarity filters (colors/references) intentionally omitted in scaffold

    return {"query": {"bool": {"must": must, "should": should}}}


def handle_search(event: Dict[str, Any]) -> Dict[str, Any]:
    headers = event.get("headers") or {}
    parse_bearer(headers.get("Authorization"))
    verify_token(parse_bearer(headers.get("Authorization")), expected_typ="access")

    qp = event.get("queryStringParameters") or {}
    limit = int(qp.get("limit", "25"))
    next_token = qp.get("nextToken")
    partial = qp.get("partial", "false").lower() == "true"

    body = json.loads((event.get("body") or "{}"))
    filters = SearchRequest.model_validate(body)
    query = _build_query(filters, partial)

    from_ = 0  # decode nextToken if needed; omitted
    os_res = svc.search(query, from_, limit)
    hits = os_res.get("hits", {}).get("hits", [])
    total = os_res.get("hits", {}).get("total", {}).get("value", 0)
    results = [
        {
            "id": h.get("_source", {}).get("id"),
            "name": h.get("_source", {}).get("name"),
            "image": h.get("_source", {}).get("image"),
            "match": int(h.get("_score", 0) * 10),
        }
        for h in hits
    ]
    return response(200, {"total": total, "nextToken": None, "results": results})
