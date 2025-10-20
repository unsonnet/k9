# GET `/user`

List users (paginated).
Only for administrator role.

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
<!-- Schema End -->

## Response 200

OK — users listed

### Body (`application/json`)

<!-- Schema Begin -->
<!-- import read.user as user -->
| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| total | `integer` | required | Total registered users |
| nextToken | `string` | optional | Pagination cursor for next page (`Base64`) |
| users | array[``user.profile``] | required | Registered users |
<!-- Schema End -->

## Response 401

Unauthorized — missing or invalid `Authorization` header (`Unauthorized`)

## Response 403

Forbidden — insufficient permissions (`Forbidden`)

## Response 500

Internal server error (`InternalServerError`)
