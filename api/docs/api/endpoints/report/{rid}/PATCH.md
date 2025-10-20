# PATCH `/report/{rid}`

Update report fields.
Only provided fields are changed.

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
| rid | `string` | required | Report ID (`UUID`) |
<!-- Schema End -->

### Body (`application/json`)

<!-- Schema Begin -->
<!-- import update.report as report -->
``report.report``
<!-- Schema End -->

## Response 200

OK — report updated

### Body (`application/json`)

<!-- Schema Begin -->
<!-- import read.report as report -->
``report.report``
<!-- Schema End -->

## Response 400

Bad request — invalid request payload (`InvalidRequest`)

## Response 401

Unauthorized — missing or invalid `Authorization` header (`Unauthorized`)

## Response 403

Forbidden — insufficient permissions (`Forbidden`)

## Response 404

Not found — report does not exist (`NotFound`)

## Response 500

Internal server error (`InternalServerError`)