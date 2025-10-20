# GET `/report`

List reports authored by user (paginated).

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
| limit | `integer` | optional | Maximum reports per page. Default: `25` |
| nextToken | `string` | optional | Pagination cursor (`Base64`) |
| author | `string` | optional | User ID (`UUID`). Default: caller |
<!-- Schema End -->

## Response 200

OK — reports listed

### Body (`application/json`)

<!-- Schema Begin -->
<!-- import read.report as report -->
| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| total | `integer` | required | Total reports |
| nextToken | `string` | optional | Pagination cursor for next page (`Base64`) |
| reports | array[``report.reportSummary``] | required | Report summaries |
<!-- Schema End -->

## Response 401

Unauthorized — missing or invalid `Authorization` header (`Unauthorized`)

## Response 403

Forbidden — insufficient permissions (`Forbidden`)

## Response 404

Not found — user does not exist (`NotFound`)

## Response 500

Internal server error (`InternalServerError`)