# API Reference

# Table of Contents

- [Auth API](#auth-api)
  - [POST /auth/forgot](#post-authforgot)
  - [POST /auth/login](#post-authlogin)
  - [POST /auth/logout](#post-authlogout)
  - [POST /auth/refresh](#post-authrefresh)
  - [POST /auth/reset](#post-authreset)


# Auth API


### Table of Contents

- [POST /auth/forgot](#post-authforgot)
  - [Request](#post-authforgot-request)
  - [Response 204](#post-authforgot-response-204)
  - [Response 400](#post-authforgot-response-400)
  - [Response 404](#post-authforgot-response-404)
  - [Response 500](#post-authforgot-response-500)
- [POST /auth/login](#post-authlogin)
  - [Request](#post-authlogin-request)
  - [Response 200](#post-authlogin-response-200)
  - [Response 202](#post-authlogin-response-202)
  - [Response 400](#post-authlogin-response-400)
  - [Response 401](#post-authlogin-response-401)
  - [Response 403](#post-authlogin-response-403)
  - [Response 404](#post-authlogin-response-404)
  - [Response 500](#post-authlogin-response-500)
- [POST /auth/logout](#post-authlogout)
  - [Request](#post-authlogout-request)
  - [Response 204](#post-authlogout-response-204)
  - [Response 401](#post-authlogout-response-401)
  - [Response 500](#post-authlogout-response-500)
- [POST /auth/refresh](#post-authrefresh)
  - [Request](#post-authrefresh-request)
  - [Response 200](#post-authrefresh-response-200)
  - [Response 400](#post-authrefresh-response-400)
  - [Response 401](#post-authrefresh-response-401)
  - [Response 500](#post-authrefresh-response-500)
- [POST /auth/reset](#post-authreset)
  - [Request](#post-authreset-request)
  - [Response 204](#post-authreset-response-204)
  - [Response 400](#post-authreset-response-400)
  - [Response 404](#post-authreset-response-404)
  - [Response 410](#post-authreset-response-410)
  - [Response 500](#post-authreset-response-500)

[Back to Top](#table-of-contents)



## POST /auth/forgot


> Request password reset for user account.

<a id="post-authforgot-request"></a>
### Request


#### Body


##### Content-Type: `application/json`


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **username** | `string` | ✅ | User name |

<a id="post-authforgot-response-204"></a>
### Response 204


> No content — password reset link sent to email

<a id="post-authforgot-response-400"></a>
### Response 400


> Bad request — invalid request payload (`InvalidRequest`)

<a id="post-authforgot-response-404"></a>
### Response 404


> Not found — user with email does not exist (`NotFound`)

<a id="post-authforgot-response-500"></a>
### Response 500


> Internal server error (`InternalServerError`)


[Back to Auth API](#auth-api)

## POST /auth/login


> Authenticate user with username and password.

<a id="post-authlogin-request"></a>
### Request


#### Body


##### Content-Type: `application/json`


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **username** | `string` | ✅ | User name |
> | **password** | `string` | ✅ | User password |

<a id="post-authlogin-response-200"></a>
### Response 200


> OK — user logged in

#### Body


##### Content-Type: `application/json`


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **user** | `string` | ✅ | User ID (`UUID`) |
> | **accessToken** | `string` | ✅ | JWT access token |
> | **refreshToken** | `string` | ✅ | JWT refresh token |
> | **expiresIn** | `integer` | ✅ | Access token expiry (`seconds`) |

<a id="post-authlogin-response-202"></a>
### Response 202


> Accepted — new password required

#### Body


##### Content-Type: `application/json`

<a id="post-authlogin-response-400"></a>
### Response 400


> Bad request — invalid request payload (`InvalidRequest`)

<a id="post-authlogin-response-401"></a>
### Response 401


> Unauthorized — invalid credentials (`Unauthorized`)

<a id="post-authlogin-response-403"></a>
### Response 403


> Forbidden — user not confirmed (`UserNotConfirmed`)

<a id="post-authlogin-response-404"></a>
### Response 404


> Not found — user does not exist (`UserNotFound`)

<a id="post-authlogin-response-500"></a>
### Response 500


> Internal server error (`InternalServerError`)


[Back to Auth API](#auth-api)

## POST /auth/logout


> Logout user and invalidate tokens.

<a id="post-authlogout-request"></a>
### Request


#### Headers


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **Authorization** | `string` | ✅ | Bearer `JWT` access token |

<a id="post-authlogout-response-204"></a>
### Response 204


> No content — user logged out

<a id="post-authlogout-response-401"></a>
### Response 401


> Unauthorized — missing or invalid `Authorization` header (`Unauthorized`)

<a id="post-authlogout-response-500"></a>
### Response 500


> Internal server error (`InternalServerError`)


[Back to Auth API](#auth-api)

## POST /auth/refresh


> Refresh access token using refresh token.

<a id="post-authrefresh-request"></a>
### Request


#### Body


##### Content-Type: `application/json`


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **username** | `string` | ✅ | User name |
> | **refreshToken** | `string` | ✅ | JWT refresh token |

<a id="post-authrefresh-response-200"></a>
### Response 200


> OK — token refreshed

#### Body


##### Content-Type: `application/json`


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **user** | `string` | ✅ | User ID (`UUID`) |
> | **accessToken** | `string` | ✅ | JWT access token |
> | **refreshToken** | `string` | ✅ | JWT refresh token |
> | **expiresIn** | `integer` | ✅ | Access token expiry (`seconds`) |

<a id="post-authrefresh-response-400"></a>
### Response 400


> Bad request — invalid request payload (`InvalidRequest`)

<a id="post-authrefresh-response-401"></a>
### Response 401


> Unauthorized — invalid or expired refresh token (`Unauthorized`)

<a id="post-authrefresh-response-500"></a>
### Response 500


> Internal server error (`InternalServerError`)


[Back to Auth API](#auth-api)

## POST /auth/reset


> Reset user password.

<a id="post-authreset-request"></a>
### Request


#### Body


##### Content-Type: `application/json`


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **username** | `string` | ✅ | User name |
> | **session** | `string` | ✅ | Session token |
> | **newPassword** | `string` | ✅ | New password |

<a id="post-authreset-response-204"></a>
### Response 204


> No content — password reset

<a id="post-authreset-response-400"></a>
### Response 400


> Bad request — invalid request payload or verification code (`InvalidRequest`)

<a id="post-authreset-response-404"></a>
### Response 404


> Not found — user with email does not exist (`NotFound`)

<a id="post-authreset-response-410"></a>
### Response 410


> Gone — verification code or session expired (`CodeExpired`, `SessionExpired`)

<a id="post-authreset-response-500"></a>
### Response 500


> Internal server error (`InternalServerError`)


[Back to Auth API](#auth-api)
