# PATCH `/user/{uid}/password`

Update user password.

## Request

### Headers

<!-- Schema Begin -->
| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| Authorization | `string` | required | Bearer `JWT` access token |
<!-- Schema End -->

### Path Parameters

<!-- Schema Begin -->
| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| uid | `string` | required | User ID (`UUID`) |
<!-- Schema End -->

### Body (`application/json`)

<!-- Schema Begin -->
<!-- import update.user as user -->
``user.password``
<!-- Schema End -->

## Response 204

No content — password updated

## Response 400

Bad request — invalid request payload (`InvalidRequest`)

## Response 401

Unauthorized — missing or invalid `Authorization` header (`Unauthorized`)

## Response 403

Forbidden — insufficient permissions or incorrect current password (`Forbidden`)

## Response 404

Not found — user does not exist (`NotFound`)

## Response 500

Internal server error (`InternalServerError`)
