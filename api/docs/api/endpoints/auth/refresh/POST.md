# POST `/auth/refresh`

Refresh access token using refresh token.

## Request

### Body (`application/json`)

<!-- Schema Begin -->
<!-- import auth -->
``auth.refresh``
<!-- Schema End -->

## Response 200

OK — token refreshed

### Body (`application/json`)

<!-- Schema Begin -->
<!-- import auth -->
``auth.session``
<!-- Schema End -->

## Response 400

Bad request — invalid request payload (`InvalidRequest`)

## Response 404

Not found — user does not exist (`NotFound`)

## Response 410

Gone — expired refresh token (`TokenExpired`)

## Response 500

Internal server error (`InternalServerError`)
