# POST `/auth/reset`

Reset user password.

## Request

### Body (`application/json`)

<!-- Schema Begin -->
<!-- import auth -->
``auth.reset``
<!-- Schema End -->

## Response 204

No content — password reset

## Response 400

Bad request — invalid request payload (`InvalidRequest`)

## Response 404

Not found — user does not exist (`NotFound`)

## Response 410

Gone — expired verification code or session token (`TokenExpired`)

## Response 500

Internal server error (`InternalServerError`)
