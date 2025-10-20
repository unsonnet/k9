# POST `/user`

Create a new user.
Only for administrator role.

## Request

### Headers

<!-- Schema Begin -->
| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| Authorization | `string` | required | Bearer `JWT` access token |
<!-- Schema End -->

### Body (`application/json`)

<!-- Schema Begin -->
<!-- import create.user as user -->
``user.profile``
<!-- Schema End -->

## Response 201

Created — user created successfully

### Body (`application/json`)

<!-- Schema Begin -->
<!-- import read.user as user -->
``user.profile``
<!-- Schema End -->

## Response 400

Bad request — invalid request payload (`InvalidRequest`)

## Response 401

Unauthorized — missing or invalid `Authorization` header (`Unauthorized`)

## Response 403

Forbidden — insufficient permissions (`Forbidden`)

## Response 409

Conflict — user with email already exists (`Conflict`)

## Response 500

Internal server error (`InternalServerError`)
