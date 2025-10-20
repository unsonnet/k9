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
> 
> > ##### `name` schema
> > 
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **brand** | `string` | — | Brand name |
> > | **series** | `string` | — | Series name |
> > | **model** | `string` | — | Model name |
>

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
> 
> > ##### `name` schema
> > 
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **brand** | `string` | — | Brand name |
> > | **series** | `string` | — | Series name |
> > | **model** | `string` | — | Model name |
> 
> 
> > ##### `format` schema
> > 
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **id** | `string` | ✅ | Format ID (`UUID`) |
> > | **aspect** | `string` | ✅ | Aspect ratio (`length`:`width`) |
> > | **length** | `dimension` | — | Longest dimension |
> > | **width** | `dimension` | — | Shortest dimension |
> > | **thickness** | `dimension` | — | Thickness dimension |
> > | **vendors** | array[`vendor`] | — | Vendor listings for this format |
> > 
> > > ##### `dimension` schema
> > > 
> > > | Field | Type | Required | Description |
> > > |:------|:-----|:--------:|:------------|
> > > | **value** | `integer` | ✅ | Dimension value |
> > > | **unit** | `string` | ✅ | Dimension unit (e.g. `mm`, `in`) |
> > 
> > 
> > > ##### `vendor` schema
> > > 
> > > | Field | Type | Required | Description |
> > > |:------|:-----|:--------:|:------------|
> > > | **id** | `string` | ✅ | Vendor ID (`UUID`) |
> > > | **sku** | `string` | ✅ | Vendor `SKU` |
> > > | **store** | `string` | ✅ | Vendor name |
> > > | **name** | `string` | ✅ | Listing name |
> > > | **price** | `currency` | — | Unit price |
> > > | **discontinued** | `boolean` | — | Listing discontinued flag |
> > > | **url** | `string` | — | Vendor product `URL` |
> > > 
> > > > ##### `currency` schema
> > > > 
> > > > | Field | Type | Required | Description |
> > > > |:------|:-----|:--------:|:------------|
> > > > | **value** | `integer` | ✅ | Currency value (minor units) |
> > > > | **unit** | `string` | ✅ | Currency code (e.g. `USD`, `CAD`) |
> > >
> >
> 
> 
> > ##### `image` schema
> > 
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **id** | `string` | ✅ | Image ID (`UUID`) |
> > | **url** | `string` | ✅ | Presigned `URL` for normalized image (`PNG`) |
>

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
> 
> > ##### `name` schema
> > 
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **brand** | `string` | — | Brand name |
> > | **series** | `string` | — | Series name |
> > | **model** | `string` | — | Model name |
> 
> 
> > ##### `format` schema
> > 
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **id** | `string` | ✅ | Format ID (`UUID`) |
> > | **aspect** | `string` | ✅ | Aspect ratio (`length`:`width`) |
> > | **length** | `dimension` | — | Longest dimension |
> > | **width** | `dimension` | — | Shortest dimension |
> > | **thickness** | `dimension` | — | Thickness dimension |
> > | **vendors** | array[`vendor`] | — | Vendor listings for this format |
> > 
> > > ##### `dimension` schema
> > > 
> > > | Field | Type | Required | Description |
> > > |:------|:-----|:--------:|:------------|
> > > | **value** | `integer` | ✅ | Dimension value |
> > > | **unit** | `string` | ✅ | Dimension unit (e.g. `mm`, `in`) |
> > 
> > 
> > > ##### `vendor` schema
> > > 
> > > | Field | Type | Required | Description |
> > > |:------|:-----|:--------:|:------------|
> > > | **id** | `string` | ✅ | Vendor ID (`UUID`) |
> > > | **sku** | `string` | ✅ | Vendor `SKU` |
> > > | **store** | `string` | ✅ | Vendor name |
> > > | **name** | `string` | ✅ | Listing name |
> > > | **price** | `currency` | — | Unit price |
> > > | **discontinued** | `boolean` | — | Listing discontinued flag |
> > > | **url** | `string` | — | Vendor product `URL` |
> > > 
> > > > ##### `currency` schema
> > > > 
> > > > | Field | Type | Required | Description |
> > > > |:------|:-----|:--------:|:------------|
> > > > | **value** | `integer` | ✅ | Currency value (minor units) |
> > > > | **unit** | `string` | ✅ | Currency code (e.g. `USD`, `CAD`) |
> > >
> >
> 
> 
> > ##### `image` schema
> > 
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **id** | `string` | ✅ | Image ID (`UUID`) |
> > | **url** | `string` | ✅ | Presigned `URL` for normalized image (`PNG`) |
>

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
> 
> > ##### `name` schema
> > 
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **brand** | `string` \| `null` | — | Brand name |
> > | **series** | `string` \| `null` | — | Series name |
> > | **model** | `string` \| `null` | — | Model name |
>

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
> 
> > ##### `name` schema
> > 
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **brand** | `string` | — | Brand name |
> > | **series** | `string` | — | Series name |
> > | **model** | `string` | — | Model name |
> 
> 
> > ##### `format` schema
> > 
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **id** | `string` | ✅ | Format ID (`UUID`) |
> > | **aspect** | `string` | ✅ | Aspect ratio (`length`:`width`) |
> > | **length** | `dimension` | — | Longest dimension |
> > | **width** | `dimension` | — | Shortest dimension |
> > | **thickness** | `dimension` | — | Thickness dimension |
> > | **vendors** | array[`vendor`] | — | Vendor listings for this format |
> > 
> > > ##### `dimension` schema
> > > 
> > > | Field | Type | Required | Description |
> > > |:------|:-----|:--------:|:------------|
> > > | **value** | `integer` | ✅ | Dimension value |
> > > | **unit** | `string` | ✅ | Dimension unit (e.g. `mm`, `in`) |
> > 
> > 
> > > ##### `vendor` schema
> > > 
> > > | Field | Type | Required | Description |
> > > |:------|:-----|:--------:|:------------|
> > > | **id** | `string` | ✅ | Vendor ID (`UUID`) |
> > > | **sku** | `string` | ✅ | Vendor `SKU` |
> > > | **store** | `string` | ✅ | Vendor name |
> > > | **name** | `string` | ✅ | Listing name |
> > > | **price** | `currency` | — | Unit price |
> > > | **discontinued** | `boolean` | — | Listing discontinued flag |
> > > | **url** | `string` | — | Vendor product `URL` |
> > > 
> > > > ##### `currency` schema
> > > > 
> > > > | Field | Type | Required | Description |
> > > > |:------|:-----|:--------:|:------------|
> > > > | **value** | `integer` | ✅ | Currency value (minor units) |
> > > > | **unit** | `string` | ✅ | Currency code (e.g. `USD`, `CAD`) |
> > >
> >
> 
> 
> > ##### `image` schema
> > 
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **id** | `string` | ✅ | Image ID (`UUID`) |
> > | **url** | `string` | ✅ | Presigned `URL` for normalized image (`PNG`) |
>

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
> 
> > ##### `dimension` schema
> > 
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **value** | `integer` | ✅ | Dimension value |
> > | **unit** | `string` | ✅ | Dimension unit (e.g. `mm`, `in`) |
>

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
> 
> > ##### `dimension` schema
> > 
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **value** | `integer` | ✅ | Dimension value |
> > | **unit** | `string` | ✅ | Dimension unit (e.g. `mm`, `in`) |
> 
> 
> > ##### `vendor` schema
> > 
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **id** | `string` | ✅ | Vendor ID (`UUID`) |
> > | **sku** | `string` | ✅ | Vendor `SKU` |
> > | **store** | `string` | ✅ | Vendor name |
> > | **name** | `string` | ✅ | Listing name |
> > | **price** | `currency` | — | Unit price |
> > | **discontinued** | `boolean` | — | Listing discontinued flag |
> > | **url** | `string` | — | Vendor product `URL` |
> > 
> > > ##### `currency` schema
> > > 
> > > | Field | Type | Required | Description |
> > > |:------|:-----|:--------:|:------------|
> > > | **value** | `integer` | ✅ | Currency value (minor units) |
> > > | **unit** | `string` | ✅ | Currency code (e.g. `USD`, `CAD`) |
> >
>

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
> 
> > ##### `dimension` schema
> > 
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **value** | `integer` | ✅ | Dimension value |
> > | **unit** | `string` | ✅ | Dimension unit (e.g. `mm`, `in`) |
>

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
> 
> > ##### `dimension` schema
> > 
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **value** | `integer` | ✅ | Dimension value |
> > | **unit** | `string` | ✅ | Dimension unit (e.g. `mm`, `in`) |
> 
> 
> > ##### `vendor` schema
> > 
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **id** | `string` | ✅ | Vendor ID (`UUID`) |
> > | **sku** | `string` | ✅ | Vendor `SKU` |
> > | **store** | `string` | ✅ | Vendor name |
> > | **name** | `string` | ✅ | Listing name |
> > | **price** | `currency` | — | Unit price |
> > | **discontinued** | `boolean` | — | Listing discontinued flag |
> > | **url** | `string` | — | Vendor product `URL` |
> > 
> > > ##### `currency` schema
> > > 
> > > | Field | Type | Required | Description |
> > > |:------|:-----|:--------:|:------------|
> > > | **value** | `integer` | ✅ | Currency value (minor units) |
> > > | **unit** | `string` | ✅ | Currency code (e.g. `USD`, `CAD`) |
> >
>

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
> 
> > ##### `currency` schema
> > 
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **value** | `integer` | ✅ | Currency value (minor units) |
> > | **unit** | `string` | ✅ | Currency code (e.g. `USD`, `CAD`) |
>

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
> 
> > ##### `currency` schema
> > 
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **value** | `integer` | ✅ | Currency value (minor units) |
> > | **unit** | `string` | ✅ | Currency code (e.g. `USD`, `CAD`) |
>

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
> 
> > ##### `currency` schema
> > 
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **value** | `integer` | ✅ | Currency value (minor units) |
> > | **unit** | `string` | ✅ | Currency code (e.g. `USD`, `CAD`) |
>

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
> 
> > ##### `currency` schema
> > 
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **value** | `integer` | ✅ | Currency value (minor units) |
> > | **unit** | `string` | ✅ | Currency code (e.g. `USD`, `CAD`) |
>

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
