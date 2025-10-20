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

Bad request — invalid request payload or verification code (`InvalidRequest`)

## Response 404

Not found — user with email does not exist (`NotFound`)

## Response 410

Gone — verification code or session expired (`CodeExpired`, `SessionExpired`)

## Response 500

Internal server error (`InternalServerError`)
