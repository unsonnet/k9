# POST `/auth/logout`

Logout user and invalidate tokens.

## Request

### Headers

<!-- Schema Begin -->
| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| Authorization | `string` | required | Bearer `JWT` access token |
<!-- Schema End -->

## Response 204

No content — user logged out

## Response 401

Unauthorized — missing or invalid `Authorization` header (`Unauthorized`)

## Response 500

Internal server error (`InternalServerError`)
