# POST `/search`

Search products (paginated).
Only provided fields are filtered.

## Request

### Headers

<!-- Schema Begin -->
| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| Authorization | `string` | required | Bearer `JWT` access token |
<!-- Schema End -->

### Query Parameters

<!-- Schema Begin -->
| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| limit | `integer` | optional | Maximum results per page. Default: `25` |
| nextToken | `string` | optional | Pagination cursor (`Base64`) |
| partial | `boolean` | optional | Include undefined fields. Default: `false` |
<!-- Schema End -->

### Body (`application/json`)

<!-- Schema Begin -->
<!-- import create.search as search -->
``search.query``
<!-- Schema End -->

## Response 200

OK — database queried

### Body (`application/json`)

<!-- Schema Begin -->
<!-- import read.search as search -->
| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| total | `integer` | required | Total matching products |
| nextToken | `string` | optional | Pagination cursor for next page (`Base64`) |
| results | array[``search.productSummary``] | required | Matching product summaries |
<!-- Schema End -->

## Response 400

Bad request — invalid filter payload (`InvalidRequest`)

## Response 401

Unauthorized — missing or invalid `Authorization` header (`Unauthorized`)

## Response 403

Forbidden — insufficient permissions (`Forbidden`)

## Response 404

Not found — referenced products do not exist (`NotFound`)

## Response 500

Internal server error (`InternalServerError`)
