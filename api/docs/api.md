# API Reference

# Table of Contents

- [Auth API](#auth-api)
  - [POST /auth/forgot](#post-authforgot)
  - [POST /auth/login](#post-authlogin)
  - [POST /auth/logout](#post-authlogout)
  - [POST /auth/refresh](#post-authrefresh)
  - [POST /auth/reset](#post-authreset)
- [Product API](#product-api)
  - [POST /product](#post-product)
  - [GET /product/{pid}](#get-productpid)
  - [PATCH /product/{pid}](#patch-productpid)
  - [DELETE /product/{pid}](#delete-productpid)
  - [POST /product/{pid}/format](#post-productpidformat)
  - [PATCH /product/{pid}/format/{fid}](#patch-productpidformatfid)
  - [DELETE /product/{pid}/format/{fid}](#delete-productpidformatfid)
  - [POST /product/{pid}/format/{fid}/vendor](#post-productpidformatfidvendor)
  - [PATCH /product/{pid}/format/{fid}/vendor/{vid}](#patch-productpidformatfidvendorvid)
  - [DELETE /product/{pid}/format/{fid}/vendor/{vid}](#delete-productpidformatfidvendorvid)
  - [POST /product/{pid}/image](#post-productpidimage)
  - [PATCH /product/{pid}/image/{iid}](#patch-productpidimageiid)
  - [DELETE /product/{pid}/image/{iid}](#delete-productpidimageiid)
- [Report API](#report-api)
  - [GET /report](#get-report)
  - [POST /report](#post-report)
  - [GET /report/{rid}](#get-reportrid)
  - [PATCH /report/{rid}](#patch-reportrid)
  - [DELETE /report/{rid}](#delete-reportrid)
  - [PUT /report/{rid}/favorite/{pid}](#put-reportridfavoritepid)
  - [DELETE /report/{rid}/favorite/{pid}](#delete-reportridfavoritepid)
- [Search API](#search-api)
  - [POST /search](#post-search)
- [User API](#user-api)
  - [GET /user](#get-user)
  - [POST /user](#post-user)
  - [GET /user/{uid}](#get-useruid)
  - [PATCH /user/{uid}](#patch-useruid)
  - [DELETE /user/{uid}](#delete-useruid)
  - [PATCH /user/{uid}/password](#patch-useruidpassword)


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
  - [Response 404](#post-authrefresh-response-404)
  - [Response 410](#post-authrefresh-response-410)
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


> No content — password reset link sent to admin

<a id="post-authforgot-response-400"></a>
### Response 400


> Bad request — invalid request payload (`InvalidRequest`)

<a id="post-authforgot-response-404"></a>
### Response 404


> Not found — user does not exist (`NotFound`)

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


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **username** | `string` | ✅ | User name |
> | **challenge** | `string` | ✅ | Challenge type (`NEW_PASSWORD_REQUIRED`) |
> | **session** | `string` | ✅ | Session token for challenge response |

<a id="post-authlogin-response-400"></a>
### Response 400


> Bad request — invalid request payload (`InvalidRequest`)

<a id="post-authlogin-response-401"></a>
### Response 401


> Unauthorized — invalid credentials (`Unauthorized`)

<a id="post-authlogin-response-404"></a>
### Response 404


> Not found — user does not exist (`NotFound`)

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

<a id="post-authrefresh-response-404"></a>
### Response 404


> Not found — user does not exist (`NotFound`)

<a id="post-authrefresh-response-410"></a>
### Response 410


> Gone — expired refresh token (`TokenExpired`)

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


> Bad request — invalid request payload (`InvalidRequest`)

<a id="post-authreset-response-404"></a>
### Response 404


> Not found — user does not exist (`NotFound`)

<a id="post-authreset-response-410"></a>
### Response 410


> Gone — expired verification code or session token (`TokenExpired`)

<a id="post-authreset-response-500"></a>
### Response 500


> Internal server error (`InternalServerError`)


[Back to Auth API](#auth-api)

# Product API


### Table of Contents

- [POST /product](#post-product)
  - [Request](#post-product-request)
  - [Response 201](#post-product-response-201)
  - [Response 400](#post-product-response-400)
  - [Response 401](#post-product-response-401)
  - [Response 403](#post-product-response-403)
  - [Response 500](#post-product-response-500)
- [GET /product/{pid}](#get-productpid)
  - [Request](#get-productpid-request)
  - [Response 200](#get-productpid-response-200)
  - [Response 401](#get-productpid-response-401)
  - [Response 403](#get-productpid-response-403)
  - [Response 404](#get-productpid-response-404)
  - [Response 500](#get-productpid-response-500)
- [PATCH /product/{pid}](#patch-productpid)
  - [Request](#patch-productpid-request)
  - [Response 200](#patch-productpid-response-200)
  - [Response 400](#patch-productpid-response-400)
  - [Response 401](#patch-productpid-response-401)
  - [Response 403](#patch-productpid-response-403)
  - [Response 404](#patch-productpid-response-404)
  - [Response 500](#patch-productpid-response-500)
- [DELETE /product/{pid}](#delete-productpid)
  - [Request](#delete-productpid-request)
  - [Response 204](#delete-productpid-response-204)
  - [Response 401](#delete-productpid-response-401)
  - [Response 403](#delete-productpid-response-403)
  - [Response 404](#delete-productpid-response-404)
  - [Response 500](#delete-productpid-response-500)
- [POST /product/{pid}/format](#post-productpidformat)
  - [Request](#post-productpidformat-request)
  - [Response 201](#post-productpidformat-response-201)
  - [Response 400](#post-productpidformat-response-400)
  - [Response 401](#post-productpidformat-response-401)
  - [Response 404](#post-productpidformat-response-404)
  - [Response 500](#post-productpidformat-response-500)
- [PATCH /product/{pid}/format/{fid}](#patch-productpidformatfid)
  - [Request](#patch-productpidformatfid-request)
  - [Response 200](#patch-productpidformatfid-response-200)
  - [Response 400](#patch-productpidformatfid-response-400)
  - [Response 401](#patch-productpidformatfid-response-401)
  - [Response 403](#patch-productpidformatfid-response-403)
  - [Response 404](#patch-productpidformatfid-response-404)
  - [Response 500](#patch-productpidformatfid-response-500)
- [DELETE /product/{pid}/format/{fid}](#delete-productpidformatfid)
  - [Request](#delete-productpidformatfid-request)
  - [Response 204](#delete-productpidformatfid-response-204)
  - [Response 401](#delete-productpidformatfid-response-401)
  - [Response 403](#delete-productpidformatfid-response-403)
  - [Response 404](#delete-productpidformatfid-response-404)
  - [Response 500](#delete-productpidformatfid-response-500)
- [POST /product/{pid}/format/{fid}/vendor](#post-productpidformatfidvendor)
  - [Request](#post-productpidformatfidvendor-request)
  - [Response 201](#post-productpidformatfidvendor-response-201)
  - [Response 400](#post-productpidformatfidvendor-response-400)
  - [Response 401](#post-productpidformatfidvendor-response-401)
  - [Response 404](#post-productpidformatfidvendor-response-404)
  - [Response 500](#post-productpidformatfidvendor-response-500)
- [PATCH /product/{pid}/format/{fid}/vendor/{vid}](#patch-productpidformatfidvendorvid)
  - [Request](#patch-productpidformatfidvendorvid-request)
  - [Response 200](#patch-productpidformatfidvendorvid-response-200)
  - [Response 400](#patch-productpidformatfidvendorvid-response-400)
  - [Response 401](#patch-productpidformatfidvendorvid-response-401)
  - [Response 403](#patch-productpidformatfidvendorvid-response-403)
  - [Response 404](#patch-productpidformatfidvendorvid-response-404)
  - [Response 500](#patch-productpidformatfidvendorvid-response-500)
- [DELETE /product/{pid}/format/{fid}/vendor/{vid}](#delete-productpidformatfidvendorvid)
  - [Request](#delete-productpidformatfidvendorvid-request)
  - [Response 204](#delete-productpidformatfidvendorvid-response-204)
  - [Response 401](#delete-productpidformatfidvendorvid-response-401)
  - [Response 403](#delete-productpidformatfidvendorvid-response-403)
  - [Response 404](#delete-productpidformatfidvendorvid-response-404)
  - [Response 500](#delete-productpidformatfidvendorvid-response-500)
- [POST /product/{pid}/image](#post-productpidimage)
  - [Request](#post-productpidimage-request)
  - [Response 201](#post-productpidimage-response-201)
  - [Response 400](#post-productpidimage-response-400)
  - [Response 401](#post-productpidimage-response-401)
  - [Response 403](#post-productpidimage-response-403)
  - [Response 404](#post-productpidimage-response-404)
  - [Response 500](#post-productpidimage-response-500)
- [PATCH /product/{pid}/image/{iid}](#patch-productpidimageiid)
  - [Request](#patch-productpidimageiid-request)
  - [Response 200](#patch-productpidimageiid-response-200)
  - [Response 400](#patch-productpidimageiid-response-400)
  - [Response 401](#patch-productpidimageiid-response-401)
  - [Response 403](#patch-productpidimageiid-response-403)
  - [Response 404](#patch-productpidimageiid-response-404)
  - [Response 500](#patch-productpidimageiid-response-500)
- [DELETE /product/{pid}/image/{iid}](#delete-productpidimageiid)
  - [Request](#delete-productpidimageiid-request)
  - [Response 204](#delete-productpidimageiid-response-204)
  - [Response 401](#delete-productpidimageiid-response-401)
  - [Response 403](#delete-productpidimageiid-response-403)
  - [Response 404](#delete-productpidimageiid-response-404)
  - [Response 500](#delete-productpidimageiid-response-500)

[Back to Top](#table-of-contents)



## POST /product


> Create product.

<a id="post-product-request"></a>
### Request


#### Headers

> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **Authorization** | `string` | ✅ | Bearer `JWT` access token |

#### Body

##### Content-Type: `application/json`


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **name** | `name` | ✅ | Product name fields (`brand`, `series`, `model`) |
> | **category** | map[`string`→`string`] | ✅ | Product attribute map (`key`→`value`) |

> > **name schema**
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **brand** | `string` | — | Brand name |
> > | **series** | `string` | — | Series name |
> > | **model** | `string` | — | Model name |

<a id="post-product-response-201"></a>
### Response 201


> Created — product created

#### Body

##### Content-Type: `application/json`


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **id** | `string` | ✅ | Product ID (`UUID`) |
> | **name** | `name` | ✅ | Product name fields (`brand`, `series`, `model`) |
> | **category** | map[`string`→`string`] | ✅ | Product attribute map (`key`→`value`) |
> | **formats** | array[`format`] | ✅ | Available formats |
> | **images** | array[`image`] | ✅ | Normalized product images |

> > **name schema**
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **brand** | `string` | — | Brand name |
> > | **series** | `string` | — | Series name |
> > | **model** | `string` | — | Model name |

> > **format schema**
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **id** | `string` | ✅ | Format ID (`UUID`) |
> > | **aspect** | `string` | ✅ | Aspect ratio (`length`:`width`) |
> > | **length** | `dimension` | — | Longest dimension |
> > | **width** | `dimension` | — | Shortest dimension |
> > | **thickness** | `dimension` | — | Thickness dimension |
> > | **vendors** | array[`vendor`] | — | Vendor listings for this format |

> > > **dimension schema**
> > > | Field | Type | Required | Description |
> > > |:------|:-----|:--------:|:------------|
> > > | **value** | `integer` | ✅ | Dimension value |
> > > | **unit** | `string` | ✅ | Dimension unit (e.g. `mm`, `in`) |

> > > **vendor schema**
> > > | Field | Type | Required | Description |
> > > |:------|:-----|:--------:|:------------|
> > > | **id** | `string` | ✅ | Vendor ID (`UUID`) |
> > > | **sku** | `string` | ✅ | Vendor `SKU` |
> > > | **store** | `string` | ✅ | Vendor name |
> > > | **name** | `string` | ✅ | Listing name |
> > > | **price** | `currency` | — | Unit price |
> > > | **discontinued** | `boolean` | — | Listing discontinued flag |
> > > | **url** | `string` | — | Vendor product `URL` |

> > > > **currency schema**
> > > > | Field | Type | Required | Description |
> > > > |:------|:-----|:--------:|:------------|
> > > > | **value** | `integer` | ✅ | Currency value (minor units) |
> > > > | **unit** | `string` | ✅ | Currency code (e.g. `USD`, `CAD`) |

> > **image schema**
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **id** | `string` | ✅ | Image ID (`UUID`) |
> > | **url** | `string` | ✅ | Presigned `URL` for normalized image (`PNG`) |

<a id="post-product-response-400"></a>
### Response 400


> Bad request — invalid request payload (`InvalidRequest`)

<a id="post-product-response-401"></a>
### Response 401


> Unauthorized — missing or invalid `Authorization` header (`Unauthorized`)

<a id="post-product-response-403"></a>
### Response 403


> Forbidden — insufficient permissions (`Forbidden`)

<a id="post-product-response-500"></a>
### Response 500


> Internal server error (`InternalServerError`)


[Back to Product API](#product-api)

## GET /product/{pid}


> Retrieve product by ID.

<a id="get-productpid-request"></a>
### Request


#### Headers

> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **Authorization** | `string` | ✅ | Bearer `JWT` access token |

#### Path Parameters

> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **pid** | `string` | ✅ | Product ID (`UUID`) |

<a id="get-productpid-response-200"></a>
### Response 200


> OK - product retrieved

#### Body

##### Content-Type: `application/json`


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **id** | `string` | ✅ | Product ID (`UUID`) |
> | **name** | `name` | ✅ | Product name fields (`brand`, `series`, `model`) |
> | **category** | map[`string`→`string`] | ✅ | Product attribute map (`key`→`value`) |
> | **formats** | array[`format`] | ✅ | Available formats |
> | **images** | array[`image`] | ✅ | Normalized product images |

> > **name schema**
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **brand** | `string` | — | Brand name |
> > | **series** | `string` | — | Series name |
> > | **model** | `string` | — | Model name |

> > **format schema**
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **id** | `string` | ✅ | Format ID (`UUID`) |
> > | **aspect** | `string` | ✅ | Aspect ratio (`length`:`width`) |
> > | **length** | `dimension` | — | Longest dimension |
> > | **width** | `dimension` | — | Shortest dimension |
> > | **thickness** | `dimension` | — | Thickness dimension |
> > | **vendors** | array[`vendor`] | — | Vendor listings for this format |

> > > **dimension schema**
> > > | Field | Type | Required | Description |
> > > |:------|:-----|:--------:|:------------|
> > > | **value** | `integer` | ✅ | Dimension value |
> > > | **unit** | `string` | ✅ | Dimension unit (e.g. `mm`, `in`) |

> > > **vendor schema**
> > > | Field | Type | Required | Description |
> > > |:------|:-----|:--------:|:------------|
> > > | **id** | `string` | ✅ | Vendor ID (`UUID`) |
> > > | **sku** | `string` | ✅ | Vendor `SKU` |
> > > | **store** | `string` | ✅ | Vendor name |
> > > | **name** | `string` | ✅ | Listing name |
> > > | **price** | `currency` | — | Unit price |
> > > | **discontinued** | `boolean` | — | Listing discontinued flag |
> > > | **url** | `string` | — | Vendor product `URL` |

> > > > **currency schema**
> > > > | Field | Type | Required | Description |
> > > > |:------|:-----|:--------:|:------------|
> > > > | **value** | `integer` | ✅ | Currency value (minor units) |
> > > > | **unit** | `string` | ✅ | Currency code (e.g. `USD`, `CAD`) |

> > **image schema**
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **id** | `string` | ✅ | Image ID (`UUID`) |
> > | **url** | `string` | ✅ | Presigned `URL` for normalized image (`PNG`) |

<a id="get-productpid-response-401"></a>
### Response 401


> Unauthorized — missing or invalid `Authorization` header (`Unauthorized`)

<a id="get-productpid-response-403"></a>
### Response 403


> Forbidden — insufficient permissions (`Forbidden`)

<a id="get-productpid-response-404"></a>
### Response 404


> Not found — product does not exist (`NotFound`)

<a id="get-productpid-response-500"></a>
### Response 500


> Internal server error (`InternalServerError`)


[Back to Product API](#product-api)

## PATCH /product/{pid}


> Update product fields.
> Only provided fields are changed.

<a id="patch-productpid-request"></a>
### Request


#### Headers

> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **Authorization** | `string` | ✅ | Bearer `JWT` access token |

#### Path Parameters

> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **pid** | `string` | ✅ | Product ID (`UUID`) |

#### Body

##### Content-Type: `application/json`


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **name** | `name` | — | Product name fields (`brand`, `series`, `model`) |
> | **category** | map[`string`→`string` \| `null`] | — | Product attribute map (`key`→`value`) |

> > **name schema**
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **brand** | `string` \| `null` | — | Brand name |
> > | **series** | `string` \| `null` | — | Series name |
> > | **model** | `string` \| `null` | — | Model name |

<a id="patch-productpid-response-200"></a>
### Response 200


> OK - product updated

#### Body

##### Content-Type: `application/json`


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **id** | `string` | ✅ | Product ID (`UUID`) |
> | **name** | `name` | ✅ | Product name fields (`brand`, `series`, `model`) |
> | **category** | map[`string`→`string`] | ✅ | Product attribute map (`key`→`value`) |
> | **formats** | array[`format`] | ✅ | Available formats |
> | **images** | array[`image`] | ✅ | Normalized product images |

> > **name schema**
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **brand** | `string` | — | Brand name |
> > | **series** | `string` | — | Series name |
> > | **model** | `string` | — | Model name |

> > **format schema**
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **id** | `string` | ✅ | Format ID (`UUID`) |
> > | **aspect** | `string` | ✅ | Aspect ratio (`length`:`width`) |
> > | **length** | `dimension` | — | Longest dimension |
> > | **width** | `dimension` | — | Shortest dimension |
> > | **thickness** | `dimension` | — | Thickness dimension |
> > | **vendors** | array[`vendor`] | — | Vendor listings for this format |

> > > **dimension schema**
> > > | Field | Type | Required | Description |
> > > |:------|:-----|:--------:|:------------|
> > > | **value** | `integer` | ✅ | Dimension value |
> > > | **unit** | `string` | ✅ | Dimension unit (e.g. `mm`, `in`) |

> > > **vendor schema**
> > > | Field | Type | Required | Description |
> > > |:------|:-----|:--------:|:------------|
> > > | **id** | `string` | ✅ | Vendor ID (`UUID`) |
> > > | **sku** | `string` | ✅ | Vendor `SKU` |
> > > | **store** | `string` | ✅ | Vendor name |
> > > | **name** | `string` | ✅ | Listing name |
> > > | **price** | `currency` | — | Unit price |
> > > | **discontinued** | `boolean` | — | Listing discontinued flag |
> > > | **url** | `string` | — | Vendor product `URL` |

> > > > **currency schema**
> > > > | Field | Type | Required | Description |
> > > > |:------|:-----|:--------:|:------------|
> > > > | **value** | `integer` | ✅ | Currency value (minor units) |
> > > > | **unit** | `string` | ✅ | Currency code (e.g. `USD`, `CAD`) |

> > **image schema**
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **id** | `string` | ✅ | Image ID (`UUID`) |
> > | **url** | `string` | ✅ | Presigned `URL` for normalized image (`PNG`) |

<a id="patch-productpid-response-400"></a>
### Response 400


> Bad request — invalid request payload (`InvalidRequest`)

<a id="patch-productpid-response-401"></a>
### Response 401


> Unauthorized — missing or invalid `Authorization` header (`Unauthorized`)

<a id="patch-productpid-response-403"></a>
### Response 403


> Forbidden — insufficient permissions (`Forbidden`)

<a id="patch-productpid-response-404"></a>
### Response 404


> Not found — product does not exist (`NotFound`)

<a id="patch-productpid-response-500"></a>
### Response 500


> Internal server error (`InternalServerError`)


[Back to Product API](#product-api)

## DELETE /product/{pid}


> Delete product and associated data. Operation is irreversible.

<a id="delete-productpid-request"></a>
### Request


#### Headers

> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **Authorization** | `string` | ✅ | Bearer `JWT` access token |

#### Path Parameters

> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **pid** | `string` | ✅ | Product ID (`UUID`) |

<a id="delete-productpid-response-204"></a>
### Response 204


> No content — product deleted

<a id="delete-productpid-response-401"></a>
### Response 401


> Unauthorized — missing or invalid `Authorization` header (`Unauthorized`)

<a id="delete-productpid-response-403"></a>
### Response 403


> Forbidden — insufficient permissions (`Forbidden`)

<a id="delete-productpid-response-404"></a>
### Response 404


> Not found — product does not exist (`NotFound`)

<a id="delete-productpid-response-500"></a>
### Response 500


> Internal server error (`InternalServerError`)


[Back to Product API](#product-api)

## POST /product/{pid}/format


> Create product format.

<a id="post-productpidformat-request"></a>
### Request


#### Headers

> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **Authorization** | `string` | ✅ | Bearer `JWT` access token |

#### Path Parameters

> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **pid** | `string` | ✅ | Product ID (`UUID`) |

#### Body

##### Content-Type: `application/json`


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **aspect** | `string` | ✅ | Aspect ratio (`length`:`width`) |
> | **length** | `dimension` | — | Longest dimension |
> | **width** | `dimension` | — | Shortest dimension |
> | **thickness** | `dimension` | — | Thickness dimension |

> > **dimension schema**
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **value** | `integer` | ✅ | Dimension value |
> > | **unit** | `string` | ✅ | Dimension unit (e.g. `mm`, `in`) |

<a id="post-productpidformat-response-201"></a>
### Response 201


> Created — format created

#### Body

##### Content-Type: `application/json`


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **id** | `string` | ✅ | Format ID (`UUID`) |
> | **aspect** | `string` | ✅ | Aspect ratio (`length`:`width`) |
> | **length** | `dimension` | — | Longest dimension |
> | **width** | `dimension` | — | Shortest dimension |
> | **thickness** | `dimension` | — | Thickness dimension |
> | **vendors** | array[`vendor`] | — | Vendor listings for this format |

> > **dimension schema**
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **value** | `integer` | ✅ | Dimension value |
> > | **unit** | `string` | ✅ | Dimension unit (e.g. `mm`, `in`) |

> > **vendor schema**
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **id** | `string` | ✅ | Vendor ID (`UUID`) |
> > | **sku** | `string` | ✅ | Vendor `SKU` |
> > | **store** | `string` | ✅ | Vendor name |
> > | **name** | `string` | ✅ | Listing name |
> > | **price** | `currency` | — | Unit price |
> > | **discontinued** | `boolean` | — | Listing discontinued flag |
> > | **url** | `string` | — | Vendor product `URL` |

> > > **currency schema**
> > > | Field | Type | Required | Description |
> > > |:------|:-----|:--------:|:------------|
> > > | **value** | `integer` | ✅ | Currency value (minor units) |
> > > | **unit** | `string` | ✅ | Currency code (e.g. `USD`, `CAD`) |

<a id="post-productpidformat-response-400"></a>
### Response 400


> Bad request — invalid request payload or aspect mismatch (`InvalidRequest`, `MismatchedShape`)

<a id="post-productpidformat-response-401"></a>
### Response 401


> Unauthorized — missing or invalid `Authorization` header (`Unauthorized`)

<a id="post-productpidformat-response-404"></a>
### Response 404


> Not found — product does not exist (`NotFound`)

<a id="post-productpidformat-response-500"></a>
### Response 500


> Internal server error (`InternalServerError`)


[Back to Product API](#product-api)

## PATCH /product/{pid}/format/{fid}


> Update product format. Dimensions are replaced, not merged.
> Only provided fields are changed.

<a id="patch-productpidformatfid-request"></a>
### Request


#### Headers

> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **Authorization** | `string` | ✅ | Bearer `JWT` access token |

#### Path Parameters

> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **pid** | `string` | ✅ | Product ID (`UUID`) |
> | **fid** | `string` | ✅ | Format ID (`UUID`) |

#### Body

##### Content-Type: `application/json`


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **aspect** | `string` | — | Aspect ratio (`length`:`width`) |
> | **length** | `dimension` \| `null` | — | Longest dimension |
> | **width** | `dimension` \| `null` | — | Shortest dimension |
> | **thickness** | `dimension` \| `null` | — | Thickness dimension |

> > **dimension schema**
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **value** | `integer` | ✅ | Dimension value |
> > | **unit** | `string` | ✅ | Dimension unit (e.g. `mm`, `in`) |

<a id="patch-productpidformatfid-response-200"></a>
### Response 200


> OK - format updated

#### Body

##### Content-Type: `application/json`


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **id** | `string` | ✅ | Format ID (`UUID`) |
> | **aspect** | `string` | ✅ | Aspect ratio (`length`:`width`) |
> | **length** | `dimension` | — | Longest dimension |
> | **width** | `dimension` | — | Shortest dimension |
> | **thickness** | `dimension` | — | Thickness dimension |
> | **vendors** | array[`vendor`] | — | Vendor listings for this format |

> > **dimension schema**
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **value** | `integer` | ✅ | Dimension value |
> > | **unit** | `string` | ✅ | Dimension unit (e.g. `mm`, `in`) |

> > **vendor schema**
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **id** | `string` | ✅ | Vendor ID (`UUID`) |
> > | **sku** | `string` | ✅ | Vendor `SKU` |
> > | **store** | `string` | ✅ | Vendor name |
> > | **name** | `string` | ✅ | Listing name |
> > | **price** | `currency` | — | Unit price |
> > | **discontinued** | `boolean` | — | Listing discontinued flag |
> > | **url** | `string` | — | Vendor product `URL` |

> > > **currency schema**
> > > | Field | Type | Required | Description |
> > > |:------|:-----|:--------:|:------------|
> > > | **value** | `integer` | ✅ | Currency value (minor units) |
> > > | **unit** | `string` | ✅ | Currency code (e.g. `USD`, `CAD`) |

<a id="patch-productpidformatfid-response-400"></a>
### Response 400


> Bad request — invalid request payload or aspect mismatch (`InvalidRequest`, `MismatchedShape`)

<a id="patch-productpidformatfid-response-401"></a>
### Response 401


> Unauthorized — missing or invalid `Authorization` header (`Unauthorized`)

<a id="patch-productpidformatfid-response-403"></a>
### Response 403


> Forbidden — insufficient permissions (`Forbidden`)

<a id="patch-productpidformatfid-response-404"></a>
### Response 404


> Not found — product or format does not exist (`NotFound`)

<a id="patch-productpidformatfid-response-500"></a>
### Response 500


> Internal server error (`InternalServerError`)


[Back to Product API](#product-api)

## DELETE /product/{pid}/format/{fid}


> Delete product format. Operation is irreversible.

<a id="delete-productpidformatfid-request"></a>
### Request


#### Headers

> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **Authorization** | `string` | ✅ | Bearer `JWT` access token |

#### Path Parameters

> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **pid** | `string` | ✅ | Product ID (`UUID`) |
> | **fid** | `string` | ✅ | Format ID (`UUID`) |

<a id="delete-productpidformatfid-response-204"></a>
### Response 204


> No content — format deleted

<a id="delete-productpidformatfid-response-401"></a>
### Response 401


> Unauthorized — missing or invalid `Authorization` header (`Unauthorized`)

<a id="delete-productpidformatfid-response-403"></a>
### Response 403


> Forbidden — insufficient permissions (`Forbidden`)

<a id="delete-productpidformatfid-response-404"></a>
### Response 404


> Not found — product or format does not exist (`NotFound`)

<a id="delete-productpidformatfid-response-500"></a>
### Response 500


> Internal server error (`InternalServerError`)


[Back to Product API](#product-api)

## POST /product/{pid}/format/{fid}/vendor


> Create product format vendor listing.

<a id="post-productpidformatfidvendor-request"></a>
### Request


#### Headers

> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **Authorization** | `string` | ✅ | Bearer `JWT` access token |

#### Path Parameters

> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **pid** | `string` | ✅ | Product ID (`UUID`) |
> | **fid** | `string` | ✅ | Format ID (`UUID`) |

#### Body

##### Content-Type: `application/json`


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **sku** | `string` | ✅ | Vendor `SKU` |
> | **store** | `string` | ✅ | Vendor name |
> | **name** | `string` | ✅ | Listing name |
> | **price** | `currency` | — | Unit price |
> | **discontinued** | `boolean` | — | Listing discontinued flag |
> | **url** | `string` | — | Vendor product `URL` |

> > **currency schema**
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **value** | `integer` | ✅ | Currency value (minor units) |
> > | **unit** | `string` | ✅ | Currency code (e.g. `USD`, `CAD`) |

<a id="post-productpidformatfidvendor-response-201"></a>
### Response 201


> Created — vendor created

#### Body

##### Content-Type: `application/json`


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **id** | `string` | ✅ | Vendor ID (`UUID`) |
> | **sku** | `string` | ✅ | Vendor `SKU` |
> | **store** | `string` | ✅ | Vendor name |
> | **name** | `string` | ✅ | Listing name |
> | **price** | `currency` | — | Unit price |
> | **discontinued** | `boolean` | — | Listing discontinued flag |
> | **url** | `string` | — | Vendor product `URL` |

> > **currency schema**
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **value** | `integer` | ✅ | Currency value (minor units) |
> > | **unit** | `string` | ✅ | Currency code (e.g. `USD`, `CAD`) |

<a id="post-productpidformatfidvendor-response-400"></a>
### Response 400


> Bad request — invalid request payload (`InvalidRequest`)

<a id="post-productpidformatfidvendor-response-401"></a>
### Response 401


> Unauthorized — missing or invalid `Authorization` header (`Unauthorized`)

<a id="post-productpidformatfidvendor-response-404"></a>
### Response 404


> Not found — product or format does not exist (`NotFound`)

<a id="post-productpidformatfidvendor-response-500"></a>
### Response 500


> Internal server error (`InternalServerError`)


[Back to Product API](#product-api)

## PATCH /product/{pid}/format/{fid}/vendor/{vid}


> Update vendor listing. Currency is replaced, not merged.
> Only provided fields are changed.

<a id="patch-productpidformatfidvendorvid-request"></a>
### Request


#### Headers

> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **Authorization** | `string` | ✅ | Bearer `JWT` access token |

#### Path Parameters

> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **pid** | `string` | ✅ | Product ID (`UUID`) |
> | **fid** | `string` | ✅ | Format ID (`UUID`) |
> | **vid** | `string` | ✅ | Vendor ID (`UUID`) |

#### Body

##### Content-Type: `application/json`


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **sku** | `string` | — | Vendor `SKU` |
> | **store** | `string` | — | Vendor name |
> | **name** | `string` | — | Listing name |
> | **price** | `currency` \| `null` | — | Unit price |
> | **discontinued** | `boolean` \| `null` | — | Listing discontinued flag |
> | **url** | `string` \| `null` | — | Vendor product `URL` |

> > **currency schema**
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **value** | `integer` | ✅ | Currency value (minor units) |
> > | **unit** | `string` | ✅ | Currency code (e.g. `USD`, `CAD`) |

<a id="patch-productpidformatfidvendorvid-response-200"></a>
### Response 200


> OK - vendor updated

#### Body

##### Content-Type: `application/json`


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **id** | `string` | ✅ | Vendor ID (`UUID`) |
> | **sku** | `string` | ✅ | Vendor `SKU` |
> | **store** | `string` | ✅ | Vendor name |
> | **name** | `string` | ✅ | Listing name |
> | **price** | `currency` | — | Unit price |
> | **discontinued** | `boolean` | — | Listing discontinued flag |
> | **url** | `string` | — | Vendor product `URL` |

> > **currency schema**
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **value** | `integer` | ✅ | Currency value (minor units) |
> > | **unit** | `string` | ✅ | Currency code (e.g. `USD`, `CAD`) |

<a id="patch-productpidformatfidvendorvid-response-400"></a>
### Response 400


> Bad request — invalid request payload (`InvalidRequest`)

<a id="patch-productpidformatfidvendorvid-response-401"></a>
### Response 401


> Unauthorized — missing or invalid `Authorization` header (`Unauthorized`)

<a id="patch-productpidformatfidvendorvid-response-403"></a>
### Response 403


> Forbidden — insufficient permissions (`Forbidden`)

<a id="patch-productpidformatfidvendorvid-response-404"></a>
### Response 404


> Not found — product, format, or vendor does not exist (`NotFound`)

<a id="patch-productpidformatfidvendorvid-response-500"></a>
### Response 500


> Internal server error (`InternalServerError`)


[Back to Product API](#product-api)

## DELETE /product/{pid}/format/{fid}/vendor/{vid}


> Delete product format vendor listing. Operation is irreversible.

<a id="delete-productpidformatfidvendorvid-request"></a>
### Request


#### Headers

> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **Authorization** | `string` | ✅ | Bearer `JWT` access token |

#### Path Parameters

> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **pid** | `string` | ✅ | Product ID (`UUID`) |
> | **fid** | `string` | ✅ | Format ID (`UUID`) |
> | **vid** | `string` | ✅ | Vendor ID (`UUID`) |

<a id="delete-productpidformatfidvendorvid-response-204"></a>
### Response 204


> No content — vendor deleted

<a id="delete-productpidformatfidvendorvid-response-401"></a>
### Response 401


> Unauthorized — missing or invalid `Authorization` header (`Unauthorized`)

<a id="delete-productpidformatfidvendorvid-response-403"></a>
### Response 403


> Forbidden — insufficient permissions (`Forbidden`)

<a id="delete-productpidformatfidvendorvid-response-404"></a>
### Response 404


> Not found — product ID, format ID, or vendor ID does not exist (`NotFound`)

<a id="delete-productpidformatfidvendorvid-response-500"></a>
### Response 500


> Internal server error (`InternalServerError`)


[Back to Product API](#product-api)

## POST /product/{pid}/image


> Upload product image with mask and homography for normalization.

<a id="post-productpidimage-request"></a>
### Request


#### Headers

> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **Authorization** | `string` | ✅ | Bearer `JWT` access token |

#### Path Parameters

> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **pid** | `string` | ✅ | Product ID (`UUID`) |

#### Body

##### Content-Type: `multipart/form-data`


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **image** | `binary` | ✅ | `JPEG` image data |
> | **mask** | `string` | ✅ | `boolean` mask matrix (`Base64`) |
> | **hom** | `string` | ✅ | `float32[3×3]` homography matrix (`Base64`) |

<a id="post-productpidimage-response-201"></a>
### Response 201


> Created — image created

#### Body

##### Content-Type: `application/json`


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **id** | `string` | ✅ | Image ID (`UUID`) |
> | **url** | `string` | ✅ | Presigned `URL` for normalized image (`PNG`) |

<a id="post-productpidimage-response-400"></a>
### Response 400


> Bad request — invalid image data or homography (`InvalidImageFormat`, `InvalidHomography`)

<a id="post-productpidimage-response-401"></a>
### Response 401


> Unauthorized — missing or invalid `Authorization` header (`Unauthorized`)

<a id="post-productpidimage-response-403"></a>
### Response 403


> Forbidden — insufficient permissions (`Forbidden`)

<a id="post-productpidimage-response-404"></a>
### Response 404


> Not found — product does not exist (`NotFound`)

<a id="post-productpidimage-response-500"></a>
### Response 500


> Internal server error (`InternalServerError`)


[Back to Product API](#product-api)

## PATCH /product/{pid}/image/{iid}


> Update image metadata (mask and homography matrix).
> Only provided fields are changed.

<a id="patch-productpidimageiid-request"></a>
### Request


#### Headers

> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **Authorization** | `string` | ✅ | Bearer `JWT` access token |

#### Path Parameters

> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **pid** | `string` | ✅ | Product ID (`UUID`) |
> | **iid** | `string` | ✅ | Image ID (`UUID`) |

#### Body

##### Content-Type: `application/json`


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **mask** | `string` | — | `boolean` mask matrix (`Base64`) |
> | **hom** | `string` | — | `float32[3×3]` homography matrix (`Base64`) |

<a id="patch-productpidimageiid-response-200"></a>
### Response 200


> OK - image updated

#### Body

##### Content-Type: `application/json`


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **id** | `string` | ✅ | Image ID (`UUID`) |
> | **url** | `string` | ✅ | Presigned `URL` for normalized image (`PNG`) |

<a id="patch-productpidimageiid-response-400"></a>
### Response 400


> Bad request — invalid request payload or image metadata (`InvalidRequest`, `InvalidBooleanMask`, `InvalidHomography`)

<a id="patch-productpidimageiid-response-401"></a>
### Response 401


> Unauthorized — missing or invalid `Authorization` header (`Unauthorized`)

<a id="patch-productpidimageiid-response-403"></a>
### Response 403


> Forbidden — insufficient permissions (`Forbidden`)

<a id="patch-productpidimageiid-response-404"></a>
### Response 404


> Not found — product or image does not exist (`NotFound`)

<a id="patch-productpidimageiid-response-500"></a>
### Response 500


> Internal server error (`InternalServerError`)


[Back to Product API](#product-api)

## DELETE /product/{pid}/image/{iid}


> Delete product image. Operation is irreversible.

<a id="delete-productpidimageiid-request"></a>
### Request


#### Headers

> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **Authorization** | `string` | ✅ | Bearer `JWT` access token |

#### Path Parameters

> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **pid** | `string` | ✅ | Product ID (`UUID`) |
> | **iid** | `string` | ✅ | Image ID (`UUID`) |

<a id="delete-productpidimageiid-response-204"></a>
### Response 204


> No content — image deleted

<a id="delete-productpidimageiid-response-401"></a>
### Response 401


> Unauthorized — missing or invalid `Authorization` header (`Unauthorized`)

<a id="delete-productpidimageiid-response-403"></a>
### Response 403


> Forbidden — insufficient permissions (`Forbidden`)

<a id="delete-productpidimageiid-response-404"></a>
### Response 404


> Not found — product or image does not exist (`NotFound`)

<a id="delete-productpidimageiid-response-500"></a>
### Response 500


> Internal server error (`InternalServerError`)


[Back to Product API](#product-api)

# Report API


### Table of Contents

- [GET /report](#get-report)
  - [Request](#get-report-request)
  - [Response 200](#get-report-response-200)
  - [Response 401](#get-report-response-401)
  - [Response 403](#get-report-response-403)
  - [Response 404](#get-report-response-404)
  - [Response 500](#get-report-response-500)
- [POST /report](#post-report)
  - [Request](#post-report-request)
  - [Response 201](#post-report-response-201)
  - [Response 400](#post-report-response-400)
  - [Response 401](#post-report-response-401)
  - [Response 403](#post-report-response-403)
  - [Response 404](#post-report-response-404)
  - [Response 500](#post-report-response-500)
- [GET /report/{rid}](#get-reportrid)
  - [Request](#get-reportrid-request)
  - [Response 200](#get-reportrid-response-200)
  - [Response 401](#get-reportrid-response-401)
  - [Response 403](#get-reportrid-response-403)
  - [Response 404](#get-reportrid-response-404)
  - [Response 500](#get-reportrid-response-500)
- [PATCH /report/{rid}](#patch-reportrid)
  - [Request](#patch-reportrid-request)
  - [Response 200](#patch-reportrid-response-200)
  - [Response 400](#patch-reportrid-response-400)
  - [Response 401](#patch-reportrid-response-401)
  - [Response 403](#patch-reportrid-response-403)
  - [Response 404](#patch-reportrid-response-404)
  - [Response 500](#patch-reportrid-response-500)
- [DELETE /report/{rid}](#delete-reportrid)
  - [Request](#delete-reportrid-request)
  - [Response 204](#delete-reportrid-response-204)
  - [Response 401](#delete-reportrid-response-401)
  - [Response 403](#delete-reportrid-response-403)
  - [Response 404](#delete-reportrid-response-404)
  - [Response 500](#delete-reportrid-response-500)
- [PUT /report/{rid}/favorite/{pid}](#put-reportridfavoritepid)
  - [Request](#put-reportridfavoritepid-request)
  - [Response 204](#put-reportridfavoritepid-response-204)
  - [Response 401](#put-reportridfavoritepid-response-401)
  - [Response 403](#put-reportridfavoritepid-response-403)
  - [Response 404](#put-reportridfavoritepid-response-404)
  - [Response 500](#put-reportridfavoritepid-response-500)
- [DELETE /report/{rid}/favorite/{pid}](#delete-reportridfavoritepid)
  - [Request](#delete-reportridfavoritepid-request)
  - [Response 204](#delete-reportridfavoritepid-response-204)
  - [Response 401](#delete-reportridfavoritepid-response-401)
  - [Response 403](#delete-reportridfavoritepid-response-403)
  - [Response 404](#delete-reportridfavoritepid-response-404)
  - [Response 500](#delete-reportridfavoritepid-response-500)

[Back to Top](#table-of-contents)



## GET /report


> List reports authored by user (paginated).

<a id="get-report-request"></a>
### Request


#### Headers

> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **Authorization** | `string` | ✅ | Bearer `JWT` access token |

#### Query Parameters

> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **limit** | `integer` | — | Maximum reports per page. Default: `25` |
> | **nextToken** | `string` | — | Pagination cursor (`Base64`) |
> | **everyone** | `boolean` | — | List all reports (only for administrator role). Default: `false` |

<a id="get-report-response-200"></a>
### Response 200


> OK — reports listed

#### Body

##### Content-Type: `application/json`


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **total** | `integer` | ✅ | Total reports |
> | **nextToken** | `string` | — | Pagination cursor for next page (`Base64`) |
> | **reports** | array[`reportSummary`] | ✅ | Report summaries |

> > **reportSummary schema**
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **id** | `string` | ✅ | Report ID (`UUID`) |
> > | **author** | `string` | ✅ | User ID (`UUID`) |
> > | **title** | `string` | ✅ | Report title |
> > | **date** | `string` | ✅ | Creation timestamp (`UTC`) |
> > | **reference** | `productSummary` | ✅ | Reference product summary |

> > > **productSummary schema**
> > > | Field | Type | Required | Description |
> > > |:------|:-----|:--------:|:------------|
> > > | **id** | `string` | ✅ | Product ID (`UUID`) |
> > > | **name** | `name` | ✅ | Product name fields (`brand`, `series`, `model`) |
> > > | **image** | `image` | ✅ | Primary product image |

> > > > **name schema**
> > > > | Field | Type | Required | Description |
> > > > |:------|:-----|:--------:|:------------|
> > > > | **brand** | `string` | — | Brand name |
> > > > | **series** | `string` | — | Series name |
> > > > | **model** | `string` | — | Model name |

> > > > **image schema**
> > > > | Field | Type | Required | Description |
> > > > |:------|:-----|:--------:|:------------|
> > > > | **id** | `string` | ✅ | Image ID (`UUID`) |
> > > > | **url** | `string` | ✅ | Presigned `URL` for normalized image (`PNG`) |

<a id="get-report-response-401"></a>
### Response 401


> Unauthorized — missing or invalid `Authorization` header (`Unauthorized`)

<a id="get-report-response-403"></a>
### Response 403


> Forbidden — insufficient permissions (`Forbidden`)

<a id="get-report-response-404"></a>
### Response 404


> Not found — user does not exist (`NotFound`)

<a id="get-report-response-500"></a>
### Response 500


> Internal server error (`InternalServerError`)


[Back to Report API](#report-api)

## POST /report


> Create report.

<a id="post-report-request"></a>
### Request


#### Headers

> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **Authorization** | `string` | ✅ | Bearer `JWT` access token |

#### Body

##### Content-Type: `application/json`


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **title** | `string` | ✅ | Report title |
> | **reference** | `string` | ✅ | Product ID (`UUID`) |

<a id="post-report-response-201"></a>
### Response 201


> Created — report created

#### Body

##### Content-Type: `application/json`


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **id** | `string` | ✅ | Report ID (`UUID`) |
> | **author** | `string` | ✅ | User ID (`UUID`) |
> | **title** | `string` | ✅ | Report title |
> | **date** | `string` | ✅ | Creation timestamp (`UTC`) |
> | **reference** | `product` | ✅ | Reference product |
> | **favorites** | array[`product`] | — | Favorited products |

> > **product schema**
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **id** | `string` | ✅ | Product ID (`UUID`) |
> > | **name** | `name` | ✅ | Product name fields (`brand`, `series`, `model`) |
> > | **category** | map[`string`→`string`] | ✅ | Product attribute map (`key`→`value`) |
> > | **formats** | array[`format`] | ✅ | Available formats |
> > | **images** | array[`image`] | ✅ | Normalized product images |

> > > **name schema**
> > > | Field | Type | Required | Description |
> > > |:------|:-----|:--------:|:------------|
> > > | **brand** | `string` | — | Brand name |
> > > | **series** | `string` | — | Series name |
> > > | **model** | `string` | — | Model name |

> > > **format schema**
> > > | Field | Type | Required | Description |
> > > |:------|:-----|:--------:|:------------|
> > > | **id** | `string` | ✅ | Format ID (`UUID`) |
> > > | **aspect** | `string` | ✅ | Aspect ratio (`length`:`width`) |
> > > | **length** | `dimension` | — | Longest dimension |
> > > | **width** | `dimension` | — | Shortest dimension |
> > > | **thickness** | `dimension` | — | Thickness dimension |
> > > | **vendors** | array[`vendor`] | — | Vendor listings for this format |

> > > > **dimension schema**
> > > > | Field | Type | Required | Description |
> > > > |:------|:-----|:--------:|:------------|
> > > > | **value** | `integer` | ✅ | Dimension value |
> > > > | **unit** | `string` | ✅ | Dimension unit (e.g. `mm`, `in`) |

> > > > **vendor schema**
> > > > | Field | Type | Required | Description |
> > > > |:------|:-----|:--------:|:------------|
> > > > | **id** | `string` | ✅ | Vendor ID (`UUID`) |
> > > > | **sku** | `string` | ✅ | Vendor `SKU` |
> > > > | **store** | `string` | ✅ | Vendor name |
> > > > | **name** | `string` | ✅ | Listing name |
> > > > | **price** | `currency` | — | Unit price |
> > > > | **discontinued** | `boolean` | — | Listing discontinued flag |
> > > > | **url** | `string` | — | Vendor product `URL` |

> > > > > **currency schema**
> > > > > | Field | Type | Required | Description |
> > > > > |:------|:-----|:--------:|:------------|
> > > > > | **value** | `integer` | ✅ | Currency value (minor units) |
> > > > > | **unit** | `string` | ✅ | Currency code (e.g. `USD`, `CAD`) |

> > > **image schema**
> > > | Field | Type | Required | Description |
> > > |:------|:-----|:--------:|:------------|
> > > | **id** | `string` | ✅ | Image ID (`UUID`) |
> > > | **url** | `string` | ✅ | Presigned `URL` for normalized image (`PNG`) |

<a id="post-report-response-400"></a>
### Response 400


> Bad request — invalid request payload (`InvalidRequest`)

<a id="post-report-response-401"></a>
### Response 401


> Unauthorized — missing or invalid `Authorization` header (`Unauthorized`)

<a id="post-report-response-403"></a>
### Response 403


> Forbidden — insufficient permissions (`Forbidden`)

<a id="post-report-response-404"></a>
### Response 404


> Not found — referenced product does not exist (`NotFound`)

<a id="post-report-response-500"></a>
### Response 500


> Internal server error (`InternalServerError`)


[Back to Report API](#report-api)

## GET /report/{rid}


> Retrieve report by ID.

<a id="get-reportrid-request"></a>
### Request


#### Headers

> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **Authorization** | `string` | ✅ | Bearer `JWT` access token |

#### Path Parameters

> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **rid** | `string` | ✅ | Report ID (`UUID`) |

<a id="get-reportrid-response-200"></a>
### Response 200


> OK - report retrieved

#### Body

##### Content-Type: `application/json`


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **id** | `string` | ✅ | Report ID (`UUID`) |
> | **author** | `string` | ✅ | User ID (`UUID`) |
> | **title** | `string` | ✅ | Report title |
> | **date** | `string` | ✅ | Creation timestamp (`UTC`) |
> | **reference** | `product` | ✅ | Reference product |
> | **favorites** | array[`product`] | — | Favorited products |

> > **product schema**
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **id** | `string` | ✅ | Product ID (`UUID`) |
> > | **name** | `name` | ✅ | Product name fields (`brand`, `series`, `model`) |
> > | **category** | map[`string`→`string`] | ✅ | Product attribute map (`key`→`value`) |
> > | **formats** | array[`format`] | ✅ | Available formats |
> > | **images** | array[`image`] | ✅ | Normalized product images |

> > > **name schema**
> > > | Field | Type | Required | Description |
> > > |:------|:-----|:--------:|:------------|
> > > | **brand** | `string` | — | Brand name |
> > > | **series** | `string` | — | Series name |
> > > | **model** | `string` | — | Model name |

> > > **format schema**
> > > | Field | Type | Required | Description |
> > > |:------|:-----|:--------:|:------------|
> > > | **id** | `string` | ✅ | Format ID (`UUID`) |
> > > | **aspect** | `string` | ✅ | Aspect ratio (`length`:`width`) |
> > > | **length** | `dimension` | — | Longest dimension |
> > > | **width** | `dimension` | — | Shortest dimension |
> > > | **thickness** | `dimension` | — | Thickness dimension |
> > > | **vendors** | array[`vendor`] | — | Vendor listings for this format |

> > > > **dimension schema**
> > > > | Field | Type | Required | Description |
> > > > |:------|:-----|:--------:|:------------|
> > > > | **value** | `integer` | ✅ | Dimension value |
> > > > | **unit** | `string` | ✅ | Dimension unit (e.g. `mm`, `in`) |

> > > > **vendor schema**
> > > > | Field | Type | Required | Description |
> > > > |:------|:-----|:--------:|:------------|
> > > > | **id** | `string` | ✅ | Vendor ID (`UUID`) |
> > > > | **sku** | `string` | ✅ | Vendor `SKU` |
> > > > | **store** | `string` | ✅ | Vendor name |
> > > > | **name** | `string` | ✅ | Listing name |
> > > > | **price** | `currency` | — | Unit price |
> > > > | **discontinued** | `boolean` | — | Listing discontinued flag |
> > > > | **url** | `string` | — | Vendor product `URL` |

> > > > > **currency schema**
> > > > > | Field | Type | Required | Description |
> > > > > |:------|:-----|:--------:|:------------|
> > > > > | **value** | `integer` | ✅ | Currency value (minor units) |
> > > > > | **unit** | `string` | ✅ | Currency code (e.g. `USD`, `CAD`) |

> > > **image schema**
> > > | Field | Type | Required | Description |
> > > |:------|:-----|:--------:|:------------|
> > > | **id** | `string` | ✅ | Image ID (`UUID`) |
> > > | **url** | `string` | ✅ | Presigned `URL` for normalized image (`PNG`) |

<a id="get-reportrid-response-401"></a>
### Response 401


> Unauthorized — missing or invalid `Authorization` header (`Unauthorized`)

<a id="get-reportrid-response-403"></a>
### Response 403


> Forbidden — insufficient permissions (`Forbidden`)

<a id="get-reportrid-response-404"></a>
### Response 404


> Not found — report does not exist (`NotFound`)

<a id="get-reportrid-response-500"></a>
### Response 500


> Internal server error (`InternalServerError`)


[Back to Report API](#report-api)

## PATCH /report/{rid}


> Update report fields.
> Only provided fields are changed.

<a id="patch-reportrid-request"></a>
### Request


#### Headers

> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **Authorization** | `string` | ✅ | Bearer `JWT` access token |

#### Path Parameters

> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **rid** | `string` | ✅ | Report ID (`UUID`) |

#### Body

##### Content-Type: `application/json`


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **title** | `string` | — | Report title |
> | **reference** | `string` | — | Product ID (`UUID`) |

<a id="patch-reportrid-response-200"></a>
### Response 200


> OK — report updated

#### Body

##### Content-Type: `application/json`


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **id** | `string` | ✅ | Report ID (`UUID`) |
> | **author** | `string` | ✅ | User ID (`UUID`) |
> | **title** | `string` | ✅ | Report title |
> | **date** | `string` | ✅ | Creation timestamp (`UTC`) |
> | **reference** | `product` | ✅ | Reference product |
> | **favorites** | array[`product`] | — | Favorited products |

> > **product schema**
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **id** | `string` | ✅ | Product ID (`UUID`) |
> > | **name** | `name` | ✅ | Product name fields (`brand`, `series`, `model`) |
> > | **category** | map[`string`→`string`] | ✅ | Product attribute map (`key`→`value`) |
> > | **formats** | array[`format`] | ✅ | Available formats |
> > | **images** | array[`image`] | ✅ | Normalized product images |

> > > **name schema**
> > > | Field | Type | Required | Description |
> > > |:------|:-----|:--------:|:------------|
> > > | **brand** | `string` | — | Brand name |
> > > | **series** | `string` | — | Series name |
> > > | **model** | `string` | — | Model name |

> > > **format schema**
> > > | Field | Type | Required | Description |
> > > |:------|:-----|:--------:|:------------|
> > > | **id** | `string` | ✅ | Format ID (`UUID`) |
> > > | **aspect** | `string` | ✅ | Aspect ratio (`length`:`width`) |
> > > | **length** | `dimension` | — | Longest dimension |
> > > | **width** | `dimension` | — | Shortest dimension |
> > > | **thickness** | `dimension` | — | Thickness dimension |
> > > | **vendors** | array[`vendor`] | — | Vendor listings for this format |

> > > > **dimension schema**
> > > > | Field | Type | Required | Description |
> > > > |:------|:-----|:--------:|:------------|
> > > > | **value** | `integer` | ✅ | Dimension value |
> > > > | **unit** | `string` | ✅ | Dimension unit (e.g. `mm`, `in`) |

> > > > **vendor schema**
> > > > | Field | Type | Required | Description |
> > > > |:------|:-----|:--------:|:------------|
> > > > | **id** | `string` | ✅ | Vendor ID (`UUID`) |
> > > > | **sku** | `string` | ✅ | Vendor `SKU` |
> > > > | **store** | `string` | ✅ | Vendor name |
> > > > | **name** | `string` | ✅ | Listing name |
> > > > | **price** | `currency` | — | Unit price |
> > > > | **discontinued** | `boolean` | — | Listing discontinued flag |
> > > > | **url** | `string` | — | Vendor product `URL` |

> > > > > **currency schema**
> > > > > | Field | Type | Required | Description |
> > > > > |:------|:-----|:--------:|:------------|
> > > > > | **value** | `integer` | ✅ | Currency value (minor units) |
> > > > > | **unit** | `string` | ✅ | Currency code (e.g. `USD`, `CAD`) |

> > > **image schema**
> > > | Field | Type | Required | Description |
> > > |:------|:-----|:--------:|:------------|
> > > | **id** | `string` | ✅ | Image ID (`UUID`) |
> > > | **url** | `string` | ✅ | Presigned `URL` for normalized image (`PNG`) |

<a id="patch-reportrid-response-400"></a>
### Response 400


> Bad request — invalid request payload (`InvalidRequest`)

<a id="patch-reportrid-response-401"></a>
### Response 401


> Unauthorized — missing or invalid `Authorization` header (`Unauthorized`)

<a id="patch-reportrid-response-403"></a>
### Response 403


> Forbidden — insufficient permissions (`Forbidden`)

<a id="patch-reportrid-response-404"></a>
### Response 404


> Not found — report does not exist (`NotFound`)

<a id="patch-reportrid-response-500"></a>
### Response 500


> Internal server error (`InternalServerError`)


[Back to Report API](#report-api)

## DELETE /report/{rid}


> Delete report and associated data. Operation is irreversible.

<a id="delete-reportrid-request"></a>
### Request


#### Headers

> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **Authorization** | `string` | ✅ | Bearer `JWT` access token |

#### Path Parameters

> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **rid** | `string` | ✅ | Report ID (`UUID`) |

<a id="delete-reportrid-response-204"></a>
### Response 204


> No content — report deleted

<a id="delete-reportrid-response-401"></a>
### Response 401


> Unauthorized — missing or invalid `Authorization` header (`Unauthorized`)

<a id="delete-reportrid-response-403"></a>
### Response 403


> Forbidden — insufficient permissions (`Forbidden`)

<a id="delete-reportrid-response-404"></a>
### Response 404


> Not found — report does not exist (`NotFound`)

<a id="delete-reportrid-response-500"></a>
### Response 500


> Internal server error (`InternalServerError`)


[Back to Report API](#report-api)

## PUT /report/{rid}/favorite/{pid}


> Add product to report favorites. Operation is idempotent.

<a id="put-reportridfavoritepid-request"></a>
### Request


#### Headers

> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **Authorization** | `string` | ✅ | Bearer `JWT` access token |

#### Path Parameters

> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **rid** | `string` | ✅ | Report ID (`UUID`) |
> | **pid** | `string` | ✅ | Product ID (`UUID`) |

<a id="put-reportridfavoritepid-response-204"></a>
### Response 204


> No content — product favorited

<a id="put-reportridfavoritepid-response-401"></a>
### Response 401


> Unauthorized — missing or invalid `Authorization` header (`Unauthorized`)

<a id="put-reportridfavoritepid-response-403"></a>
### Response 403


> Forbidden — insufficient permissions (`Forbidden`)

<a id="put-reportridfavoritepid-response-404"></a>
### Response 404


> Not found — report or product does not exist (`NotFound`)

<a id="put-reportridfavoritepid-response-500"></a>
### Response 500


> Internal server error (`InternalServerError`)


[Back to Report API](#report-api)

## DELETE /report/{rid}/favorite/{pid}


> Remove product from report favorites. Operation is idempotent.

<a id="delete-reportridfavoritepid-request"></a>
### Request


#### Headers

> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **Authorization** | `string` | ✅ | Bearer `JWT` access token |

#### Path Parameters

> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **rid** | `string` | ✅ | Report ID (`UUID`) |
> | **pid** | `string` | ✅ | Product ID (`UUID`) |

<a id="delete-reportridfavoritepid-response-204"></a>
### Response 204


> No content — product unfavorited

<a id="delete-reportridfavoritepid-response-401"></a>
### Response 401


> Unauthorized — missing or invalid `Authorization` header (`Unauthorized`)

<a id="delete-reportridfavoritepid-response-403"></a>
### Response 403


> Forbidden — insufficient permissions (`Forbidden`)

<a id="delete-reportridfavoritepid-response-404"></a>
### Response 404


> Not found — report or product does not exist (`NotFound`)

<a id="delete-reportridfavoritepid-response-500"></a>
### Response 500


> Internal server error (`InternalServerError`)


[Back to Report API](#report-api)

# Search API


### Table of Contents

- [POST /search](#post-search)
  - [Request](#post-search-request)
  - [Response 200](#post-search-response-200)
  - [Response 400](#post-search-response-400)
  - [Response 401](#post-search-response-401)
  - [Response 403](#post-search-response-403)
  - [Response 404](#post-search-response-404)
  - [Response 500](#post-search-response-500)

[Back to Top](#table-of-contents)



## POST /search


> Search products (paginated).
> Only provided fields are filtered.

<a id="post-search-request"></a>
### Request


#### Headers

> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **Authorization** | `string` | ✅ | Bearer `JWT` access token |

#### Query Parameters

> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **limit** | `integer` | — | Maximum results per page. Default: `25` |
> | **nextToken** | `string` | — | Pagination cursor (`Base64`) |
> | **partial** | `boolean` | — | Include undefined fields. Default: `false` |

#### Body

##### Content-Type: `application/json`


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **name** | `name` | — | Fuzzy filters for product name |
> | **category** | map[`string`→array[`string`]] | — | Exact-match filters for product attributes |
> | **format** | `format` | — | Exact-match and range filters for product formats |
> | **vendor** | `vendor` | — | Fuzzy and range filters for vendor listings |
> | **colors** | array[`string`] | — | Vector-similarity filter using image colors (`HEX`) |
> | **references** | array[`string`] | — | Vector-similarity filter using product IDs (`UUID`) |

> > **name schema**
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **brand** | `string` | — | Fuzzy filter for brand name |
> > | **series** | `string` | — | Fuzzy filter for series name |
> > | **model** | `string` | — | Fuzzy filter for model name |

> > **format schema**
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **aspect** | `string` | — | Exact-match filter for aspect ratio |
> > | **length** | `dimension` | — | Range filter for longest dimension |
> > | **width** | `dimension` | — | Range filter for shortest dimension |
> > | **thickness** | `dimension` | — | Range filter for thickness dimension |

> > > **dimension schema**
> > > | Field | Type | Required | Description |
> > > |:------|:-----|:--------:|:------------|
> > > | **min** | `integer` | — | Lower inclusive bound of dimension value |
> > > | **max** | `integer` | — | Upper inclusive bound of dimension value |
> > > | **unit** | `string` | ✅ | Dimension unit (e.g. `mm`, `in`) |

> > **vendor schema**
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **sku** | `string` | — | Fuzzy filter for vendor `SKU` |
> > | **store** | array[`string`] | — | Exact-match filter for vendor name |
> > | **name** | `string` | — | Fuzzy filter for listing name |
> > | **price** | `currency` | — | Range filter for unit price |
> > | **discontinued** | `boolean` | — | Filter for listing discontinued flag |

> > > **currency schema**
> > > | Field | Type | Required | Description |
> > > |:------|:-----|:--------:|:------------|
> > > | **min** | `integer` | — | Lower inclusive bound of currency value |
> > > | **max** | `integer` | — | Upper inclusive bound of currency value |
> > > | **unit** | `string` | ✅ | Currency code (e.g. `USD`, `CAD`) |

<a id="post-search-response-200"></a>
### Response 200


> OK — database queried

#### Body

##### Content-Type: `application/json`


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **total** | `integer` | ✅ | Total matching products |
> | **nextToken** | `string` | — | Pagination cursor for next page (`Base64`) |
> | **results** | array[`productSummary`] | ✅ | Matching product summaries |

> > **productSummary schema**
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **id** | `string` | ✅ | Product ID (`UUID`) |
> > | **name** | `name` | ✅ | Product name fields (`brand`, `series`, `model`) |
> > | **image** | `image` | ✅ | Primary product image |
> > | **match** | `integer` | ✅ | Similarity score from `0` to `100` percent |

> > > **name schema**
> > > | Field | Type | Required | Description |
> > > |:------|:-----|:--------:|:------------|
> > > | **brand** | `string` | — | Brand name |
> > > | **series** | `string` | — | Series name |
> > > | **model** | `string` | — | Model name |

> > > **image schema**
> > > | Field | Type | Required | Description |
> > > |:------|:-----|:--------:|:------------|
> > > | **id** | `string` | ✅ | Image ID (`UUID`) |
> > > | **url** | `string` | ✅ | Presigned `URL` for normalized image (`PNG`) |

<a id="post-search-response-400"></a>
### Response 400


> Bad request — invalid filter payload (`InvalidRequest`)

<a id="post-search-response-401"></a>
### Response 401


> Unauthorized — missing or invalid `Authorization` header (`Unauthorized`)

<a id="post-search-response-403"></a>
### Response 403


> Forbidden — insufficient permissions (`Forbidden`)

<a id="post-search-response-404"></a>
### Response 404


> Not found — referenced products do not exist (`NotFound`)

<a id="post-search-response-500"></a>
### Response 500


> Internal server error (`InternalServerError`)


[Back to Search API](#search-api)

# User API


### Table of Contents

- [GET /user](#get-user)
  - [Request](#get-user-request)
  - [Response 200](#get-user-response-200)
  - [Response 401](#get-user-response-401)
  - [Response 403](#get-user-response-403)
  - [Response 500](#get-user-response-500)
- [POST /user](#post-user)
  - [Request](#post-user-request)
  - [Response 201](#post-user-response-201)
  - [Response 400](#post-user-response-400)
  - [Response 401](#post-user-response-401)
  - [Response 403](#post-user-response-403)
  - [Response 409](#post-user-response-409)
  - [Response 500](#post-user-response-500)
- [GET /user/{uid}](#get-useruid)
  - [Request](#get-useruid-request)
  - [Response 200](#get-useruid-response-200)
  - [Response 401](#get-useruid-response-401)
  - [Response 403](#get-useruid-response-403)
  - [Response 404](#get-useruid-response-404)
  - [Response 500](#get-useruid-response-500)
- [PATCH /user/{uid}](#patch-useruid)
  - [Request](#patch-useruid-request)
  - [Response 200](#patch-useruid-response-200)
  - [Response 400](#patch-useruid-response-400)
  - [Response 401](#patch-useruid-response-401)
  - [Response 403](#patch-useruid-response-403)
  - [Response 404](#patch-useruid-response-404)
  - [Response 409](#patch-useruid-response-409)
  - [Response 500](#patch-useruid-response-500)
- [DELETE /user/{uid}](#delete-useruid)
  - [Request](#delete-useruid-request)
  - [Response 204](#delete-useruid-response-204)
  - [Response 401](#delete-useruid-response-401)
  - [Response 403](#delete-useruid-response-403)
  - [Response 404](#delete-useruid-response-404)
  - [Response 500](#delete-useruid-response-500)
- [PATCH /user/{uid}/password](#patch-useruidpassword)
  - [Request](#patch-useruidpassword-request)
  - [Response 204](#patch-useruidpassword-response-204)
  - [Response 400](#patch-useruidpassword-response-400)
  - [Response 401](#patch-useruidpassword-response-401)
  - [Response 403](#patch-useruidpassword-response-403)
  - [Response 404](#patch-useruidpassword-response-404)
  - [Response 500](#patch-useruidpassword-response-500)

[Back to Top](#table-of-contents)



## GET /user


> List users (paginated).
> Only for administrator role.

<a id="get-user-request"></a>
### Request


#### Headers

> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **Authorization** | `string` | ✅ | Bearer `JWT` access token |

#### Query Parameters

> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **limit** | `integer` | — | Maximum results per page. Default: `25` |
> | **nextToken** | `string` | — | Pagination cursor (`Base64`) |

<a id="get-user-response-200"></a>
### Response 200


> OK — users listed

#### Body

##### Content-Type: `application/json`


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **total** | `integer` | ✅ | Total registered users |
> | **nextToken** | `string` | — | Pagination cursor for next page (`Base64`) |
> | **users** | array[`profile`] | ✅ | Registered users |

> > **profile schema**
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **id** | `string` | ✅ | User ID (`UUID`) |
> > | **username** | `string` | ✅ | Display name |
> > | **email** | `string` | ✅ | Primary email |
> > | **role** | `string` | ✅ | Permission level |
> > | **preferences** | map[`string`→`string`] | ✅ | Dashboard settings |

<a id="get-user-response-401"></a>
### Response 401


> Unauthorized — missing or invalid `Authorization` header (`Unauthorized`)

<a id="get-user-response-403"></a>
### Response 403


> Forbidden — insufficient permissions (`Forbidden`)

<a id="get-user-response-500"></a>
### Response 500


> Internal server error (`InternalServerError`)


[Back to User API](#user-api)

## POST /user


> Create a new user.
> Only for administrator role.

<a id="post-user-request"></a>
### Request


#### Headers

> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **Authorization** | `string` | ✅ | Bearer `JWT` access token |

#### Body

##### Content-Type: `application/json`


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **username** | `string` | ✅ | Display name |
> | **email** | `string` | ✅ | Primary email |
> | **role** | `string` | ✅ | Permission level |
> | **preferences** | map[`string`→`string`] | — | Dashboard settings |

<a id="post-user-response-201"></a>
### Response 201


> Created — user created successfully

#### Body

##### Content-Type: `application/json`


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **id** | `string` | ✅ | User ID (`UUID`) |
> | **username** | `string` | ✅ | Display name |
> | **email** | `string` | ✅ | Primary email |
> | **role** | `string` | ✅ | Permission level |
> | **preferences** | map[`string`→`string`] | ✅ | Dashboard settings |

<a id="post-user-response-400"></a>
### Response 400


> Bad request — invalid request payload (`InvalidRequest`)

<a id="post-user-response-401"></a>
### Response 401


> Unauthorized — missing or invalid `Authorization` header (`Unauthorized`)

<a id="post-user-response-403"></a>
### Response 403


> Forbidden — insufficient permissions (`Forbidden`)

<a id="post-user-response-409"></a>
### Response 409


> Conflict — user with email already exists (`Conflict`)

<a id="post-user-response-500"></a>
### Response 500


> Internal server error (`InternalServerError`)


[Back to User API](#user-api)

## GET /user/{uid}


> Retrieve user by ID.

<a id="get-useruid-request"></a>
### Request


#### Headers

> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **Authorization** | `string` | ✅ | Bearer `JWT` access token |

#### Path Parameters

> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **uid** | `string` | ✅ | User ID (`UUID`) |

<a id="get-useruid-response-200"></a>
### Response 200


> OK — user retrieved

#### Body

##### Content-Type: `application/json`


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **id** | `string` | ✅ | User ID (`UUID`) |
> | **username** | `string` | ✅ | Display name |
> | **email** | `string` | ✅ | Primary email |
> | **role** | `string` | ✅ | Permission level |
> | **preferences** | map[`string`→`string`] | ✅ | Dashboard settings |

<a id="get-useruid-response-401"></a>
### Response 401


> Unauthorized — missing or invalid `Authorization` header (`Unauthorized`)

<a id="get-useruid-response-403"></a>
### Response 403


> Forbidden — insufficient permissions (`Forbidden`)

<a id="get-useruid-response-404"></a>
### Response 404


> Not found — user does not exist (`NotFound`)

<a id="get-useruid-response-500"></a>
### Response 500


> Internal server error (`InternalServerError`)


[Back to User API](#user-api)

## PATCH /user/{uid}


> Update user details. Only provided fields are changed.

<a id="patch-useruid-request"></a>
### Request


#### Headers

> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **Authorization** | `string` | ✅ | Bearer `JWT` access token |

#### Path Parameters

> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **uid** | `string` | ✅ | User ID (`UUID`) |

#### Body

##### Content-Type: `application/json`


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **username** | `string` | — | Display name |
> | **email** | `string` | — | Primary email |
> | **role** | `string` | — | Permission level (only for administrator role) |
> | **preferences** | map[`string`→`string` \| `null`] | — | Dashboard settings |

<a id="patch-useruid-response-200"></a>
### Response 200


> OK — user updated

#### Body

##### Content-Type: `application/json`


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **id** | `string` | ✅ | User ID (`UUID`) |
> | **username** | `string` | ✅ | Display name |
> | **email** | `string` | ✅ | Primary email |
> | **role** | `string` | ✅ | Permission level |
> | **preferences** | map[`string`→`string`] | ✅ | Dashboard settings |

<a id="patch-useruid-response-400"></a>
### Response 400


> Bad request — invalid request payload (`InvalidRequest`)

<a id="patch-useruid-response-401"></a>
### Response 401


> Unauthorized — missing or invalid `Authorization` header (`Unauthorized`)

<a id="patch-useruid-response-403"></a>
### Response 403


> Forbidden — insufficient permissions (`Forbidden`)

<a id="patch-useruid-response-404"></a>
### Response 404


> Not found — user does not exist (`NotFound`)

<a id="patch-useruid-response-409"></a>
### Response 409


> Conflict — email already in use by another user (`Conflict`)

<a id="patch-useruid-response-500"></a>
### Response 500


> Internal server error (`InternalServerError`)


[Back to User API](#user-api)

## DELETE /user/{uid}


> Delete a user account.
> Only for administrator role.

<a id="delete-useruid-request"></a>
### Request


#### Headers

> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **Authorization** | `string` | ✅ | Bearer `JWT` access token |

#### Path Parameters

> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **uid** | `string` | ✅ | User ID (`UUID`) |

<a id="delete-useruid-response-204"></a>
### Response 204


> No content — user deleted

<a id="delete-useruid-response-401"></a>
### Response 401


> Unauthorized — missing or invalid `Authorization` header (`Unauthorized`)

<a id="delete-useruid-response-403"></a>
### Response 403


> Forbidden — insufficient permissions (`Forbidden`)

<a id="delete-useruid-response-404"></a>
### Response 404


> Not found — user does not exist (`NotFound`)

<a id="delete-useruid-response-500"></a>
### Response 500


> Internal server error (`InternalServerError`)


[Back to User API](#user-api)

## PATCH /user/{uid}/password


> Update user password.

<a id="patch-useruidpassword-request"></a>
### Request


#### Headers

> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **Authorization** | `string` | ✅ | Bearer `JWT` access token |

#### Path Parameters

> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **uid** | `string` | ✅ | User ID (`UUID`) |

#### Body

##### Content-Type: `application/json`


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **currentPassword** | `string` | ✅ | Current password |
> | **newPassword** | `string` | ✅ | New password (min 8 chars) |

<a id="patch-useruidpassword-response-204"></a>
### Response 204


> No content — password updated

<a id="patch-useruidpassword-response-400"></a>
### Response 400


> Bad request — invalid request payload (`InvalidRequest`)

<a id="patch-useruidpassword-response-401"></a>
### Response 401


> Unauthorized — missing or invalid `Authorization` header (`Unauthorized`)

<a id="patch-useruidpassword-response-403"></a>
### Response 403


> Forbidden — insufficient permissions or incorrect current password (`Forbidden`)

<a id="patch-useruidpassword-response-404"></a>
### Response 404


> Not found — user does not exist (`NotFound`)

<a id="patch-useruidpassword-response-500"></a>
### Response 500


> Internal server error (`InternalServerError`)


[Back to User API](#user-api)
