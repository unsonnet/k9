# API Reference

# Table of Contents

- [User API](#user-api)
  - [GET /user](#get-user)
  - [POST /user](#post-user)
  - [GET /user/{uid}](#get-useruid)
  - [PATCH /user/{uid}](#patch-useruid)
  - [DELETE /user/{uid}](#delete-useruid)
  - [PATCH /user/{uid}/password](#patch-useruidpassword)


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
> 
> > ##### `profile` schema
> > 
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **id** | `string` | ✅ | User ID (`UUID`) |
> > | **username** | `string` | ✅ | Display name |
> > | **email** | `string` | ✅ | Primary email |
> > | **role** | `string` | ✅ | Permission level |
> > | **preferences** | map[`string`→`string`] | ✅ | Dashboard settings |
>

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
