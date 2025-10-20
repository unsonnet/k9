# API Reference

# Table of Contents

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


# Product API


### Table of Contents

- [API Reference](#api-reference)
- [Table of Contents](#table-of-contents)
- [Product API](#product-api)
    - [Table of Contents](#table-of-contents-1)
  - [POST /product](#post-product)
    - [Request](#request)
    - [Response 200](#response-200)
    - [Response 400](#response-400)
    - [Response 401](#response-401)
    - [Response 404](#response-404)
    - [Response 500](#response-500)
  - [GET /product/{pid}](#get-productpid)
    - [Request](#request-1)
    - [Response 200](#response-200-1)
    - [Response 401](#response-401-1)
    - [Response 403](#response-403)
    - [Response 404](#response-404-1)
    - [Response 500](#response-500-1)
  - [PATCH /product/{pid}](#patch-productpid)
    - [Request](#request-2)
    - [Response 200](#response-200-2)
    - [Response 400](#response-400-1)
    - [Response 401](#response-401-2)
    - [Response 403](#response-403-1)
    - [Response 404](#response-404-2)
    - [Response 500](#response-500-2)
  - [DELETE /product/{pid}](#delete-productpid)
    - [Request](#request-3)
    - [Response 200](#response-200-3)
    - [Response 401](#response-401-3)
    - [Response 403](#response-403-2)
    - [Response 404](#response-404-3)
    - [Response 500](#response-500-3)
  - [POST /product/{pid}/format](#post-productpidformat)
    - [Request](#request-4)
    - [Response 200](#response-200-4)
    - [Response 400](#response-400-2)
    - [Response 401](#response-401-4)
    - [Response 404](#response-404-4)
    - [Response 500](#response-500-4)
  - [PATCH /product/{pid}/format/{fid}](#patch-productpidformatfid)
    - [Request](#request-5)
    - [Response 200](#response-200-5)
    - [Response 400](#response-400-3)
    - [Response 401](#response-401-5)
    - [Response 403](#response-403-3)
    - [Response 404](#response-404-5)
    - [Response 500](#response-500-5)
  - [DELETE /product/{pid}/format/{fid}](#delete-productpidformatfid)
    - [Request](#request-6)
    - [Response 200](#response-200-6)
    - [Response 400](#response-400-4)
    - [Response 401](#response-401-6)
    - [Response 403](#response-403-4)
    - [Response 404](#response-404-6)
    - [Response 500](#response-500-6)
  - [POST /product/{pid}/format/{fid}/vendor](#post-productpidformatfidvendor)
    - [Request](#request-7)
    - [Response 200](#response-200-7)
    - [Response 400](#response-400-5)
    - [Response 401](#response-401-7)
    - [Response 404](#response-404-7)
    - [Response 500](#response-500-7)
  - [PATCH /product/{pid}/format/{fid}/vendor/{vid}](#patch-productpidformatfidvendorvid)
    - [Request](#request-8)
    - [Response 200](#response-200-8)
    - [Response 400](#response-400-6)
    - [Response 401](#response-401-8)
    - [Response 403](#response-403-5)
    - [Response 404](#response-404-8)
    - [Response 500](#response-500-8)
  - [DELETE /product/{pid}/format/{fid}/vendor/{vid}](#delete-productpidformatfidvendorvid)
    - [Request](#request-9)
    - [Response 200](#response-200-9)
    - [Response 400](#response-400-7)
    - [Response 401](#response-401-9)
    - [Response 403](#response-403-6)
    - [Response 404](#response-404-9)
    - [Response 500](#response-500-9)
  - [POST /product/{pid}/image](#post-productpidimage)
    - [Request](#request-10)
    - [Response 200](#response-200-10)
    - [Response 400](#response-400-8)
    - [Response 401](#response-401-10)
    - [Response 404](#response-404-10)
    - [Response 500](#response-500-10)
  - [PATCH /product/{pid}/image/{iid}](#patch-productpidimageiid)
    - [Request](#request-11)
    - [Response 200](#response-200-11)
    - [Response 400](#response-400-9)
    - [Response 401](#response-401-11)
    - [Response 403](#response-403-7)
    - [Response 404](#response-404-11)
    - [Response 500](#response-500-11)
  - [DELETE /product/{pid}/image/{iid}](#delete-productpidimageiid)
    - [Request](#request-12)
    - [Response 200](#response-200-12)
    - [Response 400](#response-400-10)
    - [Response 401](#response-401-12)
    - [Response 403](#response-403-8)
    - [Response 404](#response-404-12)
    - [Response 500](#response-500-12)
- [Report API](#report-api)
    - [Table of Contents](#table-of-contents-2)
  - [GET /report](#get-report)
    - [Request](#request-13)
    - [Response 200](#response-200-13)
    - [Response 401](#response-401-13)
    - [Response 500](#response-500-13)
  - [POST /report](#post-report)
    - [Request](#request-14)
    - [Response 200](#response-200-14)
    - [Response 400](#response-400-11)
    - [Response 401](#response-401-14)
    - [Response 404](#response-404-13)
    - [Response 500](#response-500-14)
  - [GET /report/{rid}](#get-reportrid)
    - [Request](#request-15)
    - [Response 200](#response-200-15)
    - [Response 401](#response-401-15)
    - [Response 403](#response-403-9)
    - [Response 404](#response-404-14)
    - [Response 500](#response-500-15)
  - [PATCH /report/{rid}](#patch-reportrid)
    - [Request](#request-16)
    - [Response 200](#response-200-16)
    - [Response 400](#response-400-12)
    - [Response 401](#response-401-16)
    - [Response 403](#response-403-10)
    - [Response 404](#response-404-15)
    - [Response 500](#response-500-16)
  - [DELETE /report/{rid}](#delete-reportrid)
    - [Request](#request-17)
    - [Response 200](#response-200-17)
    - [Response 401](#response-401-17)
    - [Response 403](#response-403-11)
    - [Response 404](#response-404-16)
    - [Response 500](#response-500-17)
  - [PUT /report/{rid}/favorite/{pid}](#put-reportridfavoritepid)
    - [Request](#request-18)
    - [Response 200](#response-200-18)
    - [Response 401](#response-401-18)
    - [Response 403](#response-403-12)
    - [Response 404](#response-404-17)
    - [Response 500](#response-500-18)
  - [DELETE /report/{rid}/favorite/{pid}](#delete-reportridfavoritepid)
    - [Request](#request-19)
    - [Response 200](#response-200-19)
    - [Response 401](#response-401-19)
    - [Response 403](#response-403-13)
    - [Response 404](#response-404-18)
    - [Response 500](#response-500-19)
- [Search API](#search-api)
    - [Table of Contents](#table-of-contents-3)
  - [POST /search](#post-search)
    - [Request](#request-20)
    - [Response 200](#response-200-20)
    - [Response 400](#response-400-13)
    - [Response 401](#response-401-20)
    - [Response 500](#response-500-20)

[Back to Top](#table-of-contents)



## POST /product


> Create a product.

<a id="post-product-request"></a>
### Request


#### Headers


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **Authorization** | `string` | ✅ | Bearer JWT authentication token |

#### Body


##### Content-Type: `application/json`


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **name** | `name` | ✅ | Structured product name fields |
> | **category** | map[`string`→`string`] | ✅ | Mapping of product attributes |
> 
> > ##### `name` schema
> > 
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **brand** | `string` | — | Brand name |
> > | **series** | `string` | — | Series name |
> > | **model** | `string` | — | Model identifier |
>

<a id="post-product-response-200"></a>
### Response 200


#### Body


##### Content-Type: `application/json`


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **id** | `string` | ✅ | Product ID (UUID) |
> | **name** | `name` | ✅ | Structured product name fields |
> | **category** | map[`string`→`string`] | ✅ | Product attribute key/value map |
> | **formats** | array[`format`] | ✅ | Available size configurations |
> | **images** | array[`image`] | ✅ | Normalized product images |
> 
> > ##### `name` schema
> > 
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **brand** | `string` | — | Brand name |
> > | **series** | `string` | — | Series name |
> > | **model** | `string` | — | Model identifier |
> 
> 
> > ##### `format` schema
> > 
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **id** | `string` | ✅ | Format ID (UUID) |
> > | **aspect** | `string` | ✅ | Aspect ratio (approx `length`:`width`) |
> > | **length** | `dimension` | — | Longest dimension |
> > | **width** | `dimension` | — | Shortest dimension |
> > | **thickness** | `dimension` | — | Thickness dimension |
> > | **vendors** | array[`vendor`] | — | Vendor listings for this format |
> > 
> > > ##### `dimension` schema
> > > 
> > > | Field | Type | Required | Description |
> > > |:------|:-----|:--------:|:------------|
> > > | **value** | `integer` | ✅ | Numeric value |
> > > | **unit** | `string` | ✅ | Unit symbol (e.g. mm, in) |
> > 
> > 
> > > ##### `vendor` schema
> > > 
> > > | Field | Type | Required | Description |
> > > |:------|:-----|:--------:|:------------|
> > > | **id** | `string` | ✅ | Vendor ID (UUID) |
> > > | **sku** | `string` | ✅ | Vendor SKU |
> > > | **store** | `string` | ✅ | Vendor name |
> > > | **name** | `string` | ✅ | Listing title |
> > > | **price** | `currency` | — | Unit price object |
> > > | **discontinued** | `boolean` | — | Discontinued flag |
> > > | **url** | `string` | — | Vendor product URL |
> > > 
> > > > ##### `currency` schema
> > > > 
> > > > | Field | Type | Required | Description |
> > > > |:------|:-----|:--------:|:------------|
> > > > | **value** | `integer` | ✅ | Numeric value (minor units) |
> > > > | **unit** | `string` | ✅ | Currency code (e.g. USD, CAD) |
> > >
> >
> 
> 
> > ##### `image` schema
> > 
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **id** | `string` | ✅ | Image ID (UUID) |
> > | **url** | `string` | ✅ | Presigned URL for normalized image (PNG) |
>

<a id="post-product-response-400"></a>
### Response 400


> Bad request — malformed input (`InvalidRequest`)

<a id="post-product-response-401"></a>
### Response 401


> Unauthorized — missing or invalid credentials (`Unauthorized`)

<a id="post-product-response-404"></a>
### Response 404


> Not found — one or more referenced images do not exist (`NotFound`)

<a id="post-product-response-500"></a>
### Response 500


> Internal server error (`InternalServerError`)


[Back to Product API](#product-api)

## GET /product/{pid}


> Retrieve a product by its ID.

<a id="get-productpid-request"></a>
### Request


#### Headers


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **Authorization** | `string` | ✅ | Bearer JWT authentication token |

#### Path Parameters


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **pid** | `string` | ✅ | Product ID (`UUID`) |

<a id="get-productpid-response-200"></a>
### Response 200


#### Body


##### Content-Type: `application/json`


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **id** | `string` | ✅ | Product ID (UUID) |
> | **name** | `name` | ✅ | Structured product name fields |
> | **category** | map[`string`→`string`] | ✅ | Product attribute key/value map |
> | **formats** | array[`format`] | ✅ | Available size configurations |
> | **images** | array[`image`] | ✅ | Normalized product images |
> 
> > ##### `name` schema
> > 
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **brand** | `string` | — | Brand name |
> > | **series** | `string` | — | Series name |
> > | **model** | `string` | — | Model identifier |
> 
> 
> > ##### `format` schema
> > 
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **id** | `string` | ✅ | Format ID (UUID) |
> > | **aspect** | `string` | ✅ | Aspect ratio (approx `length`:`width`) |
> > | **length** | `dimension` | — | Longest dimension |
> > | **width** | `dimension` | — | Shortest dimension |
> > | **thickness** | `dimension` | — | Thickness dimension |
> > | **vendors** | array[`vendor`] | — | Vendor listings for this format |
> > 
> > > ##### `dimension` schema
> > > 
> > > | Field | Type | Required | Description |
> > > |:------|:-----|:--------:|:------------|
> > > | **value** | `integer` | ✅ | Numeric value |
> > > | **unit** | `string` | ✅ | Unit symbol (e.g. mm, in) |
> > 
> > 
> > > ##### `vendor` schema
> > > 
> > > | Field | Type | Required | Description |
> > > |:------|:-----|:--------:|:------------|
> > > | **id** | `string` | ✅ | Vendor ID (UUID) |
> > > | **sku** | `string` | ✅ | Vendor SKU |
> > > | **store** | `string` | ✅ | Vendor name |
> > > | **name** | `string` | ✅ | Listing title |
> > > | **price** | `currency` | — | Unit price object |
> > > | **discontinued** | `boolean` | — | Discontinued flag |
> > > | **url** | `string` | — | Vendor product URL |
> > > 
> > > > ##### `currency` schema
> > > > 
> > > > | Field | Type | Required | Description |
> > > > |:------|:-----|:--------:|:------------|
> > > > | **value** | `integer` | ✅ | Numeric value (minor units) |
> > > > | **unit** | `string` | ✅ | Currency code (e.g. USD, CAD) |
> > >
> >
> 
> 
> > ##### `image` schema
> > 
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **id** | `string` | ✅ | Image ID (UUID) |
> > | **url** | `string` | ✅ | Presigned URL for normalized image (PNG) |
>

<a id="get-productpid-response-401"></a>
### Response 401


> Unauthorized — missing or invalid credentials (`Unauthorized`)

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


> Patch product fields (partial update).

<a id="patch-productpid-request"></a>
### Request


#### Headers


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **Authorization** | `string` | ✅ | Bearer JWT authentication token |

#### Path Parameters


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **pid** | `string` | ✅ | Product ID (`UUID`) |

#### Body


##### Content-Type: `application/json`


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **name** | `name` | — | Structured product name fields |
> | **category** | map[`string`→`string` \| `null`] | — | Product attribute key/value map |
> 
> > ##### `name` schema
> > 
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **brand** | `string` \| `null` | — | Brand name |
> > | **series** | `string` \| `null` | — | Series name |
> > | **model** | `string` \| `null` | — | Model identifier |
>

<a id="patch-productpid-response-200"></a>
### Response 200


#### Body


##### Content-Type: `application/json`


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **id** | `string` | ✅ | Product ID (UUID) |
> | **name** | `name` | ✅ | Structured product name fields |
> | **category** | map[`string`→`string`] | ✅ | Product attribute key/value map |
> | **formats** | array[`format`] | ✅ | Available size configurations |
> | **images** | array[`image`] | ✅ | Normalized product images |
> 
> > ##### `name` schema
> > 
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **brand** | `string` | — | Brand name |
> > | **series** | `string` | — | Series name |
> > | **model** | `string` | — | Model identifier |
> 
> 
> > ##### `format` schema
> > 
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **id** | `string` | ✅ | Format ID (UUID) |
> > | **aspect** | `string` | ✅ | Aspect ratio (approx `length`:`width`) |
> > | **length** | `dimension` | — | Longest dimension |
> > | **width** | `dimension` | — | Shortest dimension |
> > | **thickness** | `dimension` | — | Thickness dimension |
> > | **vendors** | array[`vendor`] | — | Vendor listings for this format |
> > 
> > > ##### `dimension` schema
> > > 
> > > | Field | Type | Required | Description |
> > > |:------|:-----|:--------:|:------------|
> > > | **value** | `integer` | ✅ | Numeric value |
> > > | **unit** | `string` | ✅ | Unit symbol (e.g. mm, in) |
> > 
> > 
> > > ##### `vendor` schema
> > > 
> > > | Field | Type | Required | Description |
> > > |:------|:-----|:--------:|:------------|
> > > | **id** | `string` | ✅ | Vendor ID (UUID) |
> > > | **sku** | `string` | ✅ | Vendor SKU |
> > > | **store** | `string` | ✅ | Vendor name |
> > > | **name** | `string` | ✅ | Listing title |
> > > | **price** | `currency` | — | Unit price object |
> > > | **discontinued** | `boolean` | — | Discontinued flag |
> > > | **url** | `string` | — | Vendor product URL |
> > > 
> > > > ##### `currency` schema
> > > > 
> > > > | Field | Type | Required | Description |
> > > > |:------|:-----|:--------:|:------------|
> > > > | **value** | `integer` | ✅ | Numeric value (minor units) |
> > > > | **unit** | `string` | ✅ | Currency code (e.g. USD, CAD) |
> > >
> >
> 
> 
> > ##### `image` schema
> > 
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **id** | `string` | ✅ | Image ID (UUID) |
> > | **url** | `string` | ✅ | Presigned URL for normalized image (PNG) |
>

<a id="patch-productpid-response-400"></a>
### Response 400


> Bad request — malformed input (`InvalidRequest`)

<a id="patch-productpid-response-401"></a>
### Response 401


> Unauthorized — missing or invalid credentials (`Unauthorized`)

<a id="patch-productpid-response-403"></a>
### Response 403


> Forbidden — insufficient permissions (`Forbidden`)

<a id="patch-productpid-response-404"></a>
### Response 404


> Not found — product or referenced images not found (`NotFound`)

<a id="patch-productpid-response-500"></a>
### Response 500


> Internal server error (`InternalServerError`)


[Back to Product API](#product-api)

## DELETE /product/{pid}


> Delete a product and all associated data. Irreversible.
> Only the product owner or administrators may perform this action.

<a id="delete-productpid-request"></a>
### Request


#### Headers


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **Authorization** | `string` | ✅ | Bearer JWT authentication token |

#### Path Parameters


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **pid** | `string` | ✅ | Product ID (`UUID`) |

<a id="delete-productpid-response-200"></a>
### Response 200


> OK — product deleted

<a id="delete-productpid-response-401"></a>
### Response 401


> Unauthorized — missing or invalid credentials (`Unauthorized`)

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


> Create a format for a product.

<a id="post-productpidformat-request"></a>
### Request


#### Headers


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **Authorization** | `string` | ✅ | Bearer JWT authentication token |

#### Path Parameters


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **pid** | `string` | ✅ | Product ID (`UUID`) |

#### Body


##### Content-Type: `application/json`


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **aspect** | `string` | ✅ | Aspect ratio (approx length:width) |
> | **length** | `dimension` | — | Longest planar dimension |
> | **width** | `dimension` | — | Shortest planar dimension |
> | **thickness** | `dimension` | — | Thickness dimension |
> 
> > ##### `dimension` schema
> > 
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **value** | `integer` | ✅ | Numeric value |
> > | **unit** | `string` | ✅ | Unit symbol (e.g. mm, in) |
>

<a id="post-productpidformat-response-200"></a>
### Response 200


#### Body


##### Content-Type: `application/json`


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **id** | `string` | ✅ | Format ID (UUID) |
> | **aspect** | `string` | ✅ | Aspect ratio (approx `length`:`width`) |
> | **length** | `dimension` | — | Longest dimension |
> | **width** | `dimension` | — | Shortest dimension |
> | **thickness** | `dimension` | — | Thickness dimension |
> | **vendors** | array[`vendor`] | — | Vendor listings for this format |
> 
> > ##### `dimension` schema
> > 
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **value** | `integer` | ✅ | Numeric value |
> > | **unit** | `string` | ✅ | Unit symbol (e.g. mm, in) |
> 
> 
> > ##### `vendor` schema
> > 
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **id** | `string` | ✅ | Vendor ID (UUID) |
> > | **sku** | `string` | ✅ | Vendor SKU |
> > | **store** | `string` | ✅ | Vendor name |
> > | **name** | `string` | ✅ | Listing title |
> > | **price** | `currency` | — | Unit price object |
> > | **discontinued** | `boolean` | — | Discontinued flag |
> > | **url** | `string` | — | Vendor product URL |
> > 
> > > ##### `currency` schema
> > > 
> > > | Field | Type | Required | Description |
> > > |:------|:-----|:--------:|:------------|
> > > | **value** | `integer` | ✅ | Numeric value (minor units) |
> > > | **unit** | `string` | ✅ | Currency code (e.g. USD, CAD) |
> >
>

<a id="post-productpidformat-response-400"></a>
### Response 400


> Bad request — malformed input or aspect mismatch (`InvalidRequest`, `MismatchedShape`)

<a id="post-productpidformat-response-401"></a>
### Response 401


> Unauthorized — missing or invalid credentials (`Unauthorized`)

<a id="post-productpidformat-response-404"></a>
### Response 404


> Not found — product does not exist (`NotFound`)

<a id="post-productpidformat-response-500"></a>
### Response 500


> Internal server error (`InternalServerError`)


[Back to Product API](#product-api)

## PATCH /product/{pid}/format/{fid}


> Patch a product format (partial update). Note: dimensions are replaced, not modified.

<a id="patch-productpidformatfid-request"></a>
### Request


#### Headers


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **Authorization** | `string` | ✅ | Bearer JWT authentication token |

#### Path Parameters


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **pid** | `string` | ✅ | Product ID (`UUID`) |
> | **fid** | `string` | ✅ | Format ID (`UUID`) |

#### Body


##### Content-Type: `application/json`


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **aspect** | `string` | — | Aspect ratio (approx `length`:`width`) |
> | **length** | `dimension` \| `null` | — | Longest dimension |
> | **width** | `dimension` \| `null` | — | Shortest dimension |
> | **thickness** | `dimension` \| `null` | — | Thickness dimension |
> 
> > ##### `dimension` schema
> > 
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **value** | `integer` | ✅ | Numeric value |
> > | **unit** | `string` | ✅ | Unit symbol (e.g. `mm`, `in`) |
>

<a id="patch-productpidformatfid-response-200"></a>
### Response 200


#### Body


##### Content-Type: `application/json`


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **id** | `string` | ✅ | Format ID (UUID) |
> | **aspect** | `string` | ✅ | Aspect ratio (approx `length`:`width`) |
> | **length** | `dimension` | — | Longest dimension |
> | **width** | `dimension` | — | Shortest dimension |
> | **thickness** | `dimension` | — | Thickness dimension |
> | **vendors** | array[`vendor`] | — | Vendor listings for this format |
> 
> > ##### `dimension` schema
> > 
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **value** | `integer` | ✅ | Numeric value |
> > | **unit** | `string` | ✅ | Unit symbol (e.g. mm, in) |
> 
> 
> > ##### `vendor` schema
> > 
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **id** | `string` | ✅ | Vendor ID (UUID) |
> > | **sku** | `string` | ✅ | Vendor SKU |
> > | **store** | `string` | ✅ | Vendor name |
> > | **name** | `string` | ✅ | Listing title |
> > | **price** | `currency` | — | Unit price object |
> > | **discontinued** | `boolean` | — | Discontinued flag |
> > | **url** | `string` | — | Vendor product URL |
> > 
> > > ##### `currency` schema
> > > 
> > > | Field | Type | Required | Description |
> > > |:------|:-----|:--------:|:------------|
> > > | **value** | `integer` | ✅ | Numeric value (minor units) |
> > > | **unit** | `string` | ✅ | Currency code (e.g. USD, CAD) |
> >
>

<a id="patch-productpidformatfid-response-400"></a>
### Response 400


> Bad request — malformed input or aspect mismatch (`InvalidRequest`, `MismatchedShape`)

<a id="patch-productpidformatfid-response-401"></a>
### Response 401


> Unauthorized — missing or invalid credentials (`Unauthorized`)

<a id="patch-productpidformatfid-response-403"></a>
### Response 403


> Forbidden — insufficient permissions (`Forbidden`)

<a id="patch-productpidformatfid-response-404"></a>
### Response 404


> Not found — format or product does not exist (`NotFound`)

<a id="patch-productpidformatfid-response-500"></a>
### Response 500


> Internal server error (`InternalServerError`)


[Back to Product API](#product-api)

## DELETE /product/{pid}/format/{fid}


> Delete a product format.

<a id="delete-productpidformatfid-request"></a>
### Request


#### Headers


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **Authorization** | `string` | ✅ | Bearer JWT authentication token |

#### Path Parameters


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **pid** | `string` | ✅ | Product ID (`UUID`) |
> | **fid** | `string` | ✅ | Format ID (`UUID`) |

<a id="delete-productpidformatfid-response-200"></a>
### Response 200


> OK — format deleted

<a id="delete-productpidformatfid-response-400"></a>
### Response 400


> Bad request — malformed input (`InvalidRequest`)

<a id="delete-productpidformatfid-response-401"></a>
### Response 401


> Unauthorized — missing or invalid credentials (`Unauthorized`)

<a id="delete-productpidformatfid-response-403"></a>
### Response 403


> Forbidden — insufficient permissions (`Forbidden`)

<a id="delete-productpidformatfid-response-404"></a>
### Response 404


> Not found — format or product does not exist (`NotFound`)

<a id="delete-productpidformatfid-response-500"></a>
### Response 500


> Internal server error (`InternalServerError`)


[Back to Product API](#product-api)

## POST /product/{pid}/format/{fid}/vendor


> Create a vendor listing for a product format.

<a id="post-productpidformatfidvendor-request"></a>
### Request


#### Headers


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **Authorization** | `string` | ✅ | Bearer JWT authentication token |

#### Path Parameters


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **pid** | `string` | ✅ | Product ID (`UUID`) |
> | **fid** | `string` | ✅ | Format ID (`UUID`) |

#### Body


##### Content-Type: `application/json`


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **sku** | `string` | ✅ | Vendor product SKU |
> | **store** | `string` | ✅ | Vendor name |
> | **name** | `string` | ✅ | Listing name |
> | **price** | `currency` | — | Unit price |
> | **discontinued** | `boolean` | — | Product availability |
> | **url** | `string` | — | Vendor product page URL |
> 
> > ##### `currency` schema
> > 
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **value** | `integer` | ✅ | Numeric value (minor units) |
> > | **unit** | `string` | ✅ | Currency code (e.g. USD, CAD) |
>

<a id="post-productpidformatfidvendor-response-200"></a>
### Response 200


#### Body


##### Content-Type: `application/json`


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **id** | `string` | ✅ | Vendor ID (UUID) |
> | **sku** | `string` | ✅ | Vendor SKU |
> | **store** | `string` | ✅ | Vendor name |
> | **name** | `string` | ✅ | Listing title |
> | **price** | `currency` | — | Unit price object |
> | **discontinued** | `boolean` | — | Discontinued flag |
> | **url** | `string` | — | Vendor product URL |
> 
> > ##### `currency` schema
> > 
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **value** | `integer` | ✅ | Numeric value (minor units) |
> > | **unit** | `string` | ✅ | Currency code (e.g. USD, CAD) |
>

<a id="post-productpidformatfidvendor-response-400"></a>
### Response 400


> Bad request — malformed input (`InvalidRequest`)

<a id="post-productpidformatfidvendor-response-401"></a>
### Response 401


> Unauthorized — missing or invalid credentials (`Unauthorized`)

<a id="post-productpidformatfidvendor-response-404"></a>
### Response 404


> Not found — product or format does not exist (`NotFound`)

<a id="post-productpidformatfidvendor-response-500"></a>
### Response 500


> Internal server error (`InternalServerError`)


[Back to Product API](#product-api)

## PATCH /product/{pid}/format/{fid}/vendor/{vid}


> Patch vendor listing (partial update). Note: currency is replaced, not modified.

<a id="patch-productpidformatfidvendorvid-request"></a>
### Request


#### Headers


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **Authorization** | `string` | ✅ | Bearer JWT authentication token |

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
> | **sku** | `string` | — | Vendor SKU |
> | **store** | `string` | — | Vendor name |
> | **name** | `string` | — | Listing title |
> | **price** | `currency` \| `null` | — | Unit price object |
> | **discontinued** | `boolean` \| `null` | — | Discontinued flag |
> | **url** | `string` \| `null` | — | Vendor product URL |
> 
> > ##### `currency` schema
> > 
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **value** | `integer` | ✅ | Numeric value (minor units) |
> > | **unit** | `string` | ✅ | Currency code (e.g. USD, CAD) |
>

<a id="patch-productpidformatfidvendorvid-response-200"></a>
### Response 200


#### Body


##### Content-Type: `application/json`


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **id** | `string` | ✅ | Vendor ID (UUID) |
> | **sku** | `string` | ✅ | Vendor SKU |
> | **store** | `string` | ✅ | Vendor name |
> | **name** | `string` | ✅ | Listing title |
> | **price** | `currency` | — | Unit price object |
> | **discontinued** | `boolean` | — | Discontinued flag |
> | **url** | `string` | — | Vendor product URL |
> 
> > ##### `currency` schema
> > 
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **value** | `integer` | ✅ | Numeric value (minor units) |
> > | **unit** | `string` | ✅ | Currency code (e.g. USD, CAD) |
>

<a id="patch-productpidformatfidvendorvid-response-400"></a>
### Response 400


> Bad request — malformed input (`InvalidRequest`)

<a id="patch-productpidformatfidvendorvid-response-401"></a>
### Response 401


> Unauthorized — missing or invalid credentials (`Unauthorized`)

<a id="patch-productpidformatfidvendorvid-response-403"></a>
### Response 403


> Forbidden — insufficient permissions (`Forbidden`)

<a id="patch-productpidformatfidvendorvid-response-404"></a>
### Response 404


> Not found — vendor, format, or product not found (`NotFound`)

<a id="patch-productpidformatfidvendorvid-response-500"></a>
### Response 500


> Internal server error (`InternalServerError`)


[Back to Product API](#product-api)

## DELETE /product/{pid}/format/{fid}/vendor/{vid}


> Delete a vendor listing from a product format.

<a id="delete-productpidformatfidvendorvid-request"></a>
### Request


#### Headers


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **Authorization** | `string` | ✅ | Bearer JWT authentication token |

#### Path Parameters


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **pid** | `string` | ✅ | Product ID (`UUID`) |
> | **fid** | `string` | ✅ | Format ID (`UUID`) |
> | **vid** | `string` | ✅ | Vendor ID (`UUID`) |

<a id="delete-productpidformatfidvendorvid-response-200"></a>
### Response 200


> OK — vendor deleted

<a id="delete-productpidformatfidvendorvid-response-400"></a>
### Response 400


> Bad request — malformed input (`InvalidRequest`)

<a id="delete-productpidformatfidvendorvid-response-401"></a>
### Response 401


> Unauthorized — missing or invalid credentials (`Unauthorized`)

<a id="delete-productpidformatfidvendorvid-response-403"></a>
### Response 403


> Forbidden — insufficient permissions (`Forbidden`)

<a id="delete-productpidformatfidvendorvid-response-404"></a>
### Response 404


> Not found — vendor, format, or product not found (`NotFound`)

<a id="delete-productpidformatfidvendorvid-response-500"></a>
### Response 500


> Internal server error (`InternalServerError`)


[Back to Product API](#product-api)

## POST /product/{pid}/image


> Upload a product image with mask and homography for normalization.

<a id="post-productpidimage-request"></a>
### Request


#### Headers


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **Authorization** | `string` | ✅ | Bearer JWT authentication token |

#### Path Parameters


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **pid** | `string` | ✅ | Product ID (`UUID`) |

#### Body


##### Content-Type: `multipart/form-data`


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **image** | `binary` | ✅ | JPG image |
> | **mask** | `string` | ✅ | Base64-encoded `boolean` mask matrix |
> | **hom** | `string` | ✅ | Base64-encoded `float32[3×3]` homography matrix |

<a id="post-productpidimage-response-200"></a>
### Response 200


#### Body


##### Content-Type: `application/json`


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **id** | `string` | ✅ | Image ID (UUID) |
> | **url** | `string` | ✅ | Presigned URL for normalized image (PNG) |

<a id="post-productpidimage-response-400"></a>
### Response 400


> Bad request — invalid image or homography (`InvalidImageFormat`, `InvalidHomography`)

<a id="post-productpidimage-response-401"></a>
### Response 401


> Unauthorized — missing or invalid credentials (`Unauthorized`)

<a id="post-productpidimage-response-404"></a>
### Response 404


> Not found — product does not exist (`NotFound`)

<a id="post-productpidimage-response-500"></a>
### Response 500


> Internal server error (`InternalServerError`)


[Back to Product API](#product-api)

## PATCH /product/{pid}/image/{iid}


> Patch image metadata (mask or homography).

<a id="patch-productpidimageiid-request"></a>
### Request


#### Headers


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **Authorization** | `string` | ✅ | Bearer JWT authentication token |

#### Path Parameters


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **pid** | `string` | ✅ | Product ID (`UUID`) |
> | **iid** | `string` | ✅ | Image ID (`UUID`) |

#### Body


##### Content-Type: `application/json`


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **mask** | `string` | — | Base64-encoded boolean mask matrix |
> | **hom** | `string` | — | Base64-encoded float32[3x3] homography matrix |

<a id="patch-productpidimageiid-response-200"></a>
### Response 200


#### Body


##### Content-Type: `application/json`


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **id** | `string` | ✅ | Image ID (UUID) |
> | **url** | `string` | ✅ | Presigned URL for normalized image (PNG) |

<a id="patch-productpidimageiid-response-400"></a>
### Response 400


> Bad request — malformed input or invalid image data (`InvalidRequest`, `InvalidBooleanMask`, `InvalidHomography`)

<a id="patch-productpidimageiid-response-401"></a>
### Response 401


> Unauthorized — missing or invalid credentials (`Unauthorized`)

<a id="patch-productpidimageiid-response-403"></a>
### Response 403


> Forbidden — insufficient permissions (`Forbidden`)

<a id="patch-productpidimageiid-response-404"></a>
### Response 404


> Not found — image or product does not exist (`NotFound`)

<a id="patch-productpidimageiid-response-500"></a>
### Response 500


> Internal server error (`InternalServerError`)


[Back to Product API](#product-api)

## DELETE /product/{pid}/image/{iid}


> Delete a product image.

<a id="delete-productpidimageiid-request"></a>
### Request


#### Headers


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **Authorization** | `string` | ✅ | Bearer JWT authentication token |

#### Path Parameters


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **pid** | `string` | ✅ | Product ID (`UUID`) |
> | **iid** | `string` | ✅ | Image ID (`UUID`) |

<a id="delete-productpidimageiid-response-200"></a>
### Response 200


> OK — image deleted

<a id="delete-productpidimageiid-response-400"></a>
### Response 400


> Bad request — malformed input (`InvalidRequest`)

<a id="delete-productpidimageiid-response-401"></a>
### Response 401


> Unauthorized — missing or invalid credentials (`Unauthorized`)

<a id="delete-productpidimageiid-response-403"></a>
### Response 403


> Forbidden — insufficient permissions (`Forbidden`)

<a id="delete-productpidimageiid-response-404"></a>
### Response 404


> Not found — image or product does not exist (`NotFound`)

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
  - [Response 500](#get-report-response-500)
- [POST /report](#post-report)
  - [Request](#post-report-request)
  - [Response 200](#post-report-response-200)
  - [Response 400](#post-report-response-400)
  - [Response 401](#post-report-response-401)
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
  - [Response 200](#delete-reportrid-response-200)
  - [Response 401](#delete-reportrid-response-401)
  - [Response 403](#delete-reportrid-response-403)
  - [Response 404](#delete-reportrid-response-404)
  - [Response 500](#delete-reportrid-response-500)
- [PUT /report/{rid}/favorite/{pid}](#put-reportridfavoritepid)
  - [Request](#put-reportridfavoritepid-request)
  - [Response 200](#put-reportridfavoritepid-response-200)
  - [Response 401](#put-reportridfavoritepid-response-401)
  - [Response 403](#put-reportridfavoritepid-response-403)
  - [Response 404](#put-reportridfavoritepid-response-404)
  - [Response 500](#put-reportridfavoritepid-response-500)
- [DELETE /report/{rid}/favorite/{pid}](#delete-reportridfavoritepid)
  - [Request](#delete-reportridfavoritepid-request)
  - [Response 200](#delete-reportridfavoritepid-response-200)
  - [Response 401](#delete-reportridfavoritepid-response-401)
  - [Response 403](#delete-reportridfavoritepid-response-403)
  - [Response 404](#delete-reportridfavoritepid-response-404)
  - [Response 500](#delete-reportridfavoritepid-response-500)

[Back to Top](#table-of-contents)



## GET /report


> List reports (paginated) accessible to the authenticated user.

<a id="get-report-request"></a>
### Request


#### Headers


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **Authorization** | `string` | ✅ | Bearer JWT authentication token |

#### Query Parameters


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **limit** | `integer` | — | Max reports per page (default `25`) |
> | **nextToken** | `string` | — | Base64-encoded pagination cursor |

<a id="get-report-response-200"></a>
### Response 200


#### Body


##### Content-Type: `application/json`


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **total** | `integer` | ✅ | Total number of accessible reports |
> | **nextToken** | `string` | — | Base64-encoded pagination cursor for the next page |
> | **reports** | array[`reportSummary`] | ✅ | List of report summaries |
> 
> > ##### `reportSummary` schema
> > 
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **id** | `string` | ✅ | Report ID (`UUID`) |
> > | **author** | `string` | ✅ | Author's username |
> > | **title** | `string` | ✅ | Report title |
> > | **date** | `string` | ✅ | UTC timestamp when created |
> > | **reference** | `productSummary` | ✅ | Reference product |
> > 
> > > ##### `productSummary` schema
> > > 
> > > | Field | Type | Required | Description |
> > > |:------|:-----|:--------:|:------------|
> > > | **id** | `string` | ✅ | Product ID (`UUID`) |
> > > | **name** | `name` | ✅ | Structured product name fields |
> > > | **image** | `image` | ✅ | First product image |
> > > 
> > > > ##### `name` schema
> > > > 
> > > > | Field | Type | Required | Description |
> > > > |:------|:-----|:--------:|:------------|
> > > > | **brand** | `string` | — | Brand name |
> > > > | **series** | `string` | — | Series name |
> > > > | **model** | `string` | — | Model identifier |
> > > 
> > > 
> > > > ##### `image` schema
> > > > 
> > > > | Field | Type | Required | Description |
> > > > |:------|:-----|:--------:|:------------|
> > > > | **id** | `string` | ✅ | Image ID (UUID) |
> > > > | **url** | `string` | ✅ | Presigned URL for normalized image (PNG) |
> > >
> >
>

<a id="get-report-response-401"></a>
### Response 401


> Unauthorized — missing or invalid credentials (`Unauthorized`)

<a id="get-report-response-500"></a>
### Response 500


> Internal server error (`InternalServerError`)


[Back to Report API](#report-api)

## POST /report


> Create a report.

<a id="post-report-request"></a>
### Request


#### Headers


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **Authorization** | `string` | ✅ | Bearer JWT authentication token |

#### Body


##### Content-Type: `application/json`


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **title** | `string` | ✅ | Report title |
> | **reference** | `string` | ✅ | Reference product ID (`UUID`) |

<a id="post-report-response-200"></a>
### Response 200


#### Body


##### Content-Type: `application/json`


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **id** | `string` | ✅ | Report ID (UUID) |
> | **author** | `string` | ✅ | Author username |
> | **title** | `string` | ✅ | Report title |
> | **date** | `string` | ✅ | Creation timestamp (UTC) |
> | **reference** | `product` | ✅ | Reference product object |
> | **favorites** | array[`product`] | — | Favorited products list |
> 
> > ##### `product` schema
> > 
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **id** | `string` | ✅ | Product ID (UUID) |
> > | **name** | `name` | ✅ | Structured product name fields |
> > | **category** | map[`string`→`string`] | ✅ | Product attribute key/value map |
> > | **formats** | array[`format`] | ✅ | Available size configurations |
> > | **images** | array[`image`] | ✅ | Normalized product images |
> > 
> > > ##### `name` schema
> > > 
> > > | Field | Type | Required | Description |
> > > |:------|:-----|:--------:|:------------|
> > > | **brand** | `string` | — | Brand name |
> > > | **series** | `string` | — | Series name |
> > > | **model** | `string` | — | Model identifier |
> > 
> > 
> > > ##### `format` schema
> > > 
> > > | Field | Type | Required | Description |
> > > |:------|:-----|:--------:|:------------|
> > > | **id** | `string` | ✅ | Format ID (UUID) |
> > > | **aspect** | `string` | ✅ | Aspect ratio (approx `length`:`width`) |
> > > | **length** | `dimension` | — | Longest dimension |
> > > | **width** | `dimension` | — | Shortest dimension |
> > > | **thickness** | `dimension` | — | Thickness dimension |
> > > | **vendors** | array[`vendor`] | — | Vendor listings for this format |
> > > 
> > > > ##### `dimension` schema
> > > > 
> > > > | Field | Type | Required | Description |
> > > > |:------|:-----|:--------:|:------------|
> > > > | **value** | `integer` | ✅ | Numeric value |
> > > > | **unit** | `string` | ✅ | Unit symbol (e.g. mm, in) |
> > > 
> > > 
> > > > ##### `vendor` schema
> > > > 
> > > > | Field | Type | Required | Description |
> > > > |:------|:-----|:--------:|:------------|
> > > > | **id** | `string` | ✅ | Vendor ID (UUID) |
> > > > | **sku** | `string` | ✅ | Vendor SKU |
> > > > | **store** | `string` | ✅ | Vendor name |
> > > > | **name** | `string` | ✅ | Listing title |
> > > > | **price** | `currency` | — | Unit price object |
> > > > | **discontinued** | `boolean` | — | Discontinued flag |
> > > > | **url** | `string` | — | Vendor product URL |
> > > > 
> > > > > ##### `currency` schema
> > > > > 
> > > > > | Field | Type | Required | Description |
> > > > > |:------|:-----|:--------:|:------------|
> > > > > | **value** | `integer` | ✅ | Numeric value (minor units) |
> > > > > | **unit** | `string` | ✅ | Currency code (e.g. USD, CAD) |
> > > >
> > >
> > 
> > 
> > > ##### `image` schema
> > > 
> > > | Field | Type | Required | Description |
> > > |:------|:-----|:--------:|:------------|
> > > | **id** | `string` | ✅ | Image ID (UUID) |
> > > | **url** | `string` | ✅ | Presigned URL for normalized image (PNG) |
> >
>

<a id="post-report-response-400"></a>
### Response 400


> Bad request — malformed input (`InvalidRequest`)

<a id="post-report-response-401"></a>
### Response 401


> Unauthorized — missing or invalid credentials (`Unauthorized`)

<a id="post-report-response-404"></a>
### Response 404


> Not found — referenced images do not exist (`NotFound`)

<a id="post-report-response-500"></a>
### Response 500


> Internal server error (`InternalServerError`)


[Back to Report API](#report-api)

## GET /report/{rid}


> Retrieve a report by ID.

<a id="get-reportrid-request"></a>
### Request


#### Headers


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **Authorization** | `string` | ✅ | Bearer JWT authentication token |

#### Path Parameters


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **rid** | `string` | ✅ | Report ID (`UUID`) |

<a id="get-reportrid-response-200"></a>
### Response 200


#### Body


##### Content-Type: `application/json`


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **id** | `string` | ✅ | Report ID (UUID) |
> | **author** | `string` | ✅ | Author username |
> | **title** | `string` | ✅ | Report title |
> | **date** | `string` | ✅ | Creation timestamp (UTC) |
> | **reference** | `product` | ✅ | Reference product object |
> | **favorites** | array[`product`] | — | Favorited products list |
> 
> > ##### `product` schema
> > 
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **id** | `string` | ✅ | Product ID (UUID) |
> > | **name** | `name` | ✅ | Structured product name fields |
> > | **category** | map[`string`→`string`] | ✅ | Product attribute key/value map |
> > | **formats** | array[`format`] | ✅ | Available size configurations |
> > | **images** | array[`image`] | ✅ | Normalized product images |
> > 
> > > ##### `name` schema
> > > 
> > > | Field | Type | Required | Description |
> > > |:------|:-----|:--------:|:------------|
> > > | **brand** | `string` | — | Brand name |
> > > | **series** | `string` | — | Series name |
> > > | **model** | `string` | — | Model identifier |
> > 
> > 
> > > ##### `format` schema
> > > 
> > > | Field | Type | Required | Description |
> > > |:------|:-----|:--------:|:------------|
> > > | **id** | `string` | ✅ | Format ID (UUID) |
> > > | **aspect** | `string` | ✅ | Aspect ratio (approx `length`:`width`) |
> > > | **length** | `dimension` | — | Longest dimension |
> > > | **width** | `dimension` | — | Shortest dimension |
> > > | **thickness** | `dimension` | — | Thickness dimension |
> > > | **vendors** | array[`vendor`] | — | Vendor listings for this format |
> > > 
> > > > ##### `dimension` schema
> > > > 
> > > > | Field | Type | Required | Description |
> > > > |:------|:-----|:--------:|:------------|
> > > > | **value** | `integer` | ✅ | Numeric value |
> > > > | **unit** | `string` | ✅ | Unit symbol (e.g. mm, in) |
> > > 
> > > 
> > > > ##### `vendor` schema
> > > > 
> > > > | Field | Type | Required | Description |
> > > > |:------|:-----|:--------:|:------------|
> > > > | **id** | `string` | ✅ | Vendor ID (UUID) |
> > > > | **sku** | `string` | ✅ | Vendor SKU |
> > > > | **store** | `string` | ✅ | Vendor name |
> > > > | **name** | `string` | ✅ | Listing title |
> > > > | **price** | `currency` | — | Unit price object |
> > > > | **discontinued** | `boolean` | — | Discontinued flag |
> > > > | **url** | `string` | — | Vendor product URL |
> > > > 
> > > > > ##### `currency` schema
> > > > > 
> > > > > | Field | Type | Required | Description |
> > > > > |:------|:-----|:--------:|:------------|
> > > > > | **value** | `integer` | ✅ | Numeric value (minor units) |
> > > > > | **unit** | `string` | ✅ | Currency code (e.g. USD, CAD) |
> > > >
> > >
> > 
> > 
> > > ##### `image` schema
> > > 
> > > | Field | Type | Required | Description |
> > > |:------|:-----|:--------:|:------------|
> > > | **id** | `string` | ✅ | Image ID (UUID) |
> > > | **url** | `string` | ✅ | Presigned URL for normalized image (PNG) |
> >
>

<a id="get-reportrid-response-401"></a>
### Response 401


> Unauthorized — missing or invalid credentials (`Unauthorized`)

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


> Patch a report (partial update). Only provided fields are updated.

<a id="patch-reportrid-request"></a>
### Request


#### Headers


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **Authorization** | `string` | ✅ | Bearer JWT authentication token |

#### Path Parameters


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **rid** | `string` | ✅ | Report ID (`UUID`) |

#### Body


##### Content-Type: `application/json`


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **title** | `string` | — | Report title |
> | **reference** | `string` | — | Reference product ID (UUID) |

<a id="patch-reportrid-response-200"></a>
### Response 200


#### Body


##### Content-Type: `application/json`


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **id** | `string` | ✅ | Report ID (UUID) |
> | **author** | `string` | ✅ | Author username |
> | **title** | `string` | ✅ | Report title |
> | **date** | `string` | ✅ | Creation timestamp (UTC) |
> | **reference** | `product` | ✅ | Reference product object |
> | **favorites** | array[`product`] | — | Favorited products list |
> 
> > ##### `product` schema
> > 
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **id** | `string` | ✅ | Product ID (UUID) |
> > | **name** | `name` | ✅ | Structured product name fields |
> > | **category** | map[`string`→`string`] | ✅ | Product attribute key/value map |
> > | **formats** | array[`format`] | ✅ | Available size configurations |
> > | **images** | array[`image`] | ✅ | Normalized product images |
> > 
> > > ##### `name` schema
> > > 
> > > | Field | Type | Required | Description |
> > > |:------|:-----|:--------:|:------------|
> > > | **brand** | `string` | — | Brand name |
> > > | **series** | `string` | — | Series name |
> > > | **model** | `string` | — | Model identifier |
> > 
> > 
> > > ##### `format` schema
> > > 
> > > | Field | Type | Required | Description |
> > > |:------|:-----|:--------:|:------------|
> > > | **id** | `string` | ✅ | Format ID (UUID) |
> > > | **aspect** | `string` | ✅ | Aspect ratio (approx `length`:`width`) |
> > > | **length** | `dimension` | — | Longest dimension |
> > > | **width** | `dimension` | — | Shortest dimension |
> > > | **thickness** | `dimension` | — | Thickness dimension |
> > > | **vendors** | array[`vendor`] | — | Vendor listings for this format |
> > > 
> > > > ##### `dimension` schema
> > > > 
> > > > | Field | Type | Required | Description |
> > > > |:------|:-----|:--------:|:------------|
> > > > | **value** | `integer` | ✅ | Numeric value |
> > > > | **unit** | `string` | ✅ | Unit symbol (e.g. mm, in) |
> > > 
> > > 
> > > > ##### `vendor` schema
> > > > 
> > > > | Field | Type | Required | Description |
> > > > |:------|:-----|:--------:|:------------|
> > > > | **id** | `string` | ✅ | Vendor ID (UUID) |
> > > > | **sku** | `string` | ✅ | Vendor SKU |
> > > > | **store** | `string` | ✅ | Vendor name |
> > > > | **name** | `string` | ✅ | Listing title |
> > > > | **price** | `currency` | — | Unit price object |
> > > > | **discontinued** | `boolean` | — | Discontinued flag |
> > > > | **url** | `string` | — | Vendor product URL |
> > > > 
> > > > > ##### `currency` schema
> > > > > 
> > > > > | Field | Type | Required | Description |
> > > > > |:------|:-----|:--------:|:------------|
> > > > > | **value** | `integer` | ✅ | Numeric value (minor units) |
> > > > > | **unit** | `string` | ✅ | Currency code (e.g. USD, CAD) |
> > > >
> > >
> > 
> > 
> > > ##### `image` schema
> > > 
> > > | Field | Type | Required | Description |
> > > |:------|:-----|:--------:|:------------|
> > > | **id** | `string` | ✅ | Image ID (UUID) |
> > > | **url** | `string` | ✅ | Presigned URL for normalized image (PNG) |
> >
>

<a id="patch-reportrid-response-400"></a>
### Response 400


> Bad request — malformed input (`InvalidRequest`)

<a id="patch-reportrid-response-401"></a>
### Response 401


> Unauthorized — missing or invalid credentials (`Unauthorized`)

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


> Delete a report and all associated data. Irreversible.
> Only the report author or administrators may perform this action.

<a id="delete-reportrid-request"></a>
### Request


#### Headers


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **Authorization** | `string` | ✅ | Bearer JWT authentication token |

#### Path Parameters


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **rid** | `string` | ✅ | Report ID (`UUID`) |

<a id="delete-reportrid-response-200"></a>
### Response 200


> OK — report deleted

<a id="delete-reportrid-response-401"></a>
### Response 401


> Unauthorized — missing or invalid credentials (`Unauthorized`)

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


> Add a product to a report's favorites. Idempotent.

<a id="put-reportridfavoritepid-request"></a>
### Request


#### Headers


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **Authorization** | `string` | ✅ | Bearer JWT authentication token |

#### Path Parameters


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **rid** | `string` | ✅ | Report ID (`UUID`) |
> | **pid** | `string` | ✅ | Product ID (`UUID`) |

<a id="put-reportridfavoritepid-response-200"></a>
### Response 200


> OK — product favorited

<a id="put-reportridfavoritepid-response-401"></a>
### Response 401


> Unauthorized — missing or invalid credentials (`Unauthorized`)

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


> Remove a product from a report's favorites. Idempotent.

<a id="delete-reportridfavoritepid-request"></a>
### Request


#### Headers


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **Authorization** | `string` | ✅ | Bearer JWT authentication token |

#### Path Parameters


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **rid** | `string` | ✅ | Report ID (`UUID`) |
> | **pid** | `string` | ✅ | Product ID (`UUID`) |

<a id="delete-reportridfavoritepid-response-200"></a>
### Response 200


> OK — product unfavorited

<a id="delete-reportridfavoritepid-response-401"></a>
### Response 401


> Unauthorized — missing or invalid credentials (`Unauthorized`)

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
  - [Response 500](#post-search-response-500)

[Back to Top](#table-of-contents)



## POST /search


> Search for products using a schema-aligned filter object. Each field is a filter, not a literal value.

<a id="post-search-request"></a>
### Request


#### Headers


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **Authorization** | `string` | ✅ | Bearer JWT authentication token |

#### Query Parameters


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **limit** | `integer` | — | Max results per page (default `25`) |
> | **nextToken** | `string` | — | Base64-encoded pagination cursor |

#### Body


##### Content-Type: `application/json`


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **name** | `name` | — | Name-specific filters |
> | **category** | map[`string`→array[`string`]] | — | Category specific filters |
> | **format** | `format` | — | Format specific filters |
> | **vendor** | `vendor` | — | Vendor specific filters |
> | **image** | `image` | — | Image specific filters |
> | **references** | array[`string`] | — | Array of product ids (`UUID`) for reference |
> 
> > ##### `name` schema
> > 
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **brand** | `string` | — | Product brand |
> > | **series** | `string` | — | Product series |
> > | **model** | `string` | — | Product model |
> 
> 
> > ##### `format` schema
> > 
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **aspect** | `string` | — | Aspect ratio |
> > | **length** | `dimension` | — | Longest planar dimension |
> > | **width** | `dimension` | — | Shortest planar dimension |
> > | **thickness** | `dimension` | — | Thickness dimension |
> > | **vendors** | array[`vendor`] | — | List of vendor listings |
> > 
> > > ##### `dimension` schema
> > > 
> > > | Field | Type | Required | Description |
> > > |:------|:-----|:--------:|:------------|
> > > | **min** | `integer` | — | Min numeric value |
> > > | **max** | `integer` | — | Max numeric value |
> > > | **unit** | `string` | ✅ | Unit symbol (e.g. `mm`, `in`) |
> > 
> > 
> > > ##### `vendor` schema
> > > 
> > > | Field | Type | Required | Description |
> > > |:------|:-----|:--------:|:------------|
> > > | **sku** | `string` | — | Vendor product SKU |
> > > | **store** | array[`string`] | — | Vendor name |
> > > | **name** | `string` | — | Listing name |
> > > | **price** | `currency` | — | Unit price |
> > > | **discontinued** | `boolean` | — | Product availability |
> > > 
> > > > ##### `currency` schema
> > > > 
> > > > | Field | Type | Required | Description |
> > > > |:------|:-----|:--------:|:------------|
> > > > | **min** | `integer` | — | Min numeric value |
> > > > | **max** | `integer` | — | Max numeric value |
> > > > | **unit** | `string` | ✅ | Unit symbol (e.g. `USD`, `CAD`) |
> > >
> >
> 
> 
> > ##### `image` schema
> > 
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **color** | array[`string`] | — | Color hex codes |
>

<a id="post-search-response-200"></a>
### Response 200


#### Body


##### Content-Type: `application/json`


> | Field | Type | Required | Description |
> |:------|:-----|:--------:|:------------|
> | **total** | `integer` | ✅ | Total number of products matching the filters |
> | **nextToken** | `string` | — | Cursor for the next page of results |
> | **results** | array[`productSummary`] | ✅ | Matching product summaries |
> 
> > ##### `productSummary` schema
> > 
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **id** | `string` | ✅ | Product ID (UUID) |
> > | **name** | `name` | ✅ | Structured product name fields |
> > | **image** | `image` | ✅ | First product image |
> > 
> > > ##### `name` schema
> > > 
> > > | Field | Type | Required | Description |
> > > |:------|:-----|:--------:|:------------|
> > > | **brand** | `string` | — | Brand name |
> > > | **series** | `string` | — | Series name |
> > > | **model** | `string` | — | Model identifier |
> > 
> > 
> > > ##### `image` schema
> > > 
> > > | Field | Type | Required | Description |
> > > |:------|:-----|:--------:|:------------|
> > > | **id** | `string` | ✅ | Image ID (UUID) |
> > > | **url** | `string` | ✅ | Presigned URL for normalized image (PNG) |
> >
>

<a id="post-search-response-400"></a>
### Response 400


> Bad request — malformed filter (`InvalidRequest`)

<a id="post-search-response-401"></a>
### Response 401


> Unauthorized — missing or invalid credentials (`Unauthorized`)

<a id="post-search-response-500"></a>
### Response 500


> Internal server error (`InternalServerError`)


[Back to Search API](#search-api)
