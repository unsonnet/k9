# API Reference

# Table of Contents

- [Report API](#report-api)
  - [GET /report](#get-report)
  - [POST /report](#post-report)
  - [GET /report/{rid}](#get-reportrid)
  - [PATCH /report/{rid}](#patch-reportrid)
  - [DELETE /report/{rid}](#delete-reportrid)
  - [PUT /report/{rid}/favorite/{pid}](#put-reportridfavoritepid)
  - [DELETE /report/{rid}/favorite/{pid}](#delete-reportridfavoritepid)


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
> 
> > ##### `reportSummary` schema
> > 
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **id** | `string` | ✅ | Report ID (`UUID`) |
> > | **author** | `string` | ✅ | User ID (`UUID`) |
> > | **title** | `string` | ✅ | Report title |
> > | **date** | `string` | ✅ | Creation timestamp (`UTC`) |
> > | **reference** | `productSummary` | ✅ | Reference product summary |
> > 
> > > ##### `productSummary` schema
> > > 
> > > | Field | Type | Required | Description |
> > > |:------|:-----|:--------:|:------------|
> > > | **id** | `string` | ✅ | Product ID (`UUID`) |
> > > | **name** | `name` | ✅ | Product name fields (`brand`, `series`, `model`) |
> > > | **image** | `image` | ✅ | Primary product image |
> > > 
> > > > ##### `name` schema
> > > > 
> > > > | Field | Type | Required | Description |
> > > > |:------|:-----|:--------:|:------------|
> > > > | **brand** | `string` | — | Brand name |
> > > > | **series** | `string` | — | Series name |
> > > > | **model** | `string` | — | Model name |
> > > 
> > > 
> > > > ##### `image` schema
> > > > 
> > > > | Field | Type | Required | Description |
> > > > |:------|:-----|:--------:|:------------|
> > > > | **id** | `string` | ✅ | Image ID (`UUID`) |
> > > > | **url** | `string` | ✅ | Presigned `URL` for normalized image (`PNG`) |
> > >
> >
>

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
> 
> > ##### `product` schema
> > 
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **id** | `string` | ✅ | Product ID (`UUID`) |
> > | **name** | `name` | ✅ | Product name fields (`brand`, `series`, `model`) |
> > | **category** | map[`string`→`string`] | ✅ | Product attribute map (`key`→`value`) |
> > | **formats** | array[`format`] | ✅ | Available formats |
> > | **images** | array[`image`] | ✅ | Normalized product images |
> > 
> > > ##### `name` schema
> > > 
> > > | Field | Type | Required | Description |
> > > |:------|:-----|:--------:|:------------|
> > > | **brand** | `string` | — | Brand name |
> > > | **series** | `string` | — | Series name |
> > > | **model** | `string` | — | Model name |
> > 
> > 
> > > ##### `format` schema
> > > 
> > > | Field | Type | Required | Description |
> > > |:------|:-----|:--------:|:------------|
> > > | **id** | `string` | ✅ | Format ID (`UUID`) |
> > > | **aspect** | `string` | ✅ | Aspect ratio (`length`:`width`) |
> > > | **length** | `dimension` | — | Longest dimension |
> > > | **width** | `dimension` | — | Shortest dimension |
> > > | **thickness** | `dimension` | — | Thickness dimension |
> > > | **vendors** | array[`vendor`] | — | Vendor listings for this format |
> > > 
> > > > ##### `dimension` schema
> > > > 
> > > > | Field | Type | Required | Description |
> > > > |:------|:-----|:--------:|:------------|
> > > > | **value** | `integer` | ✅ | Dimension value |
> > > > | **unit** | `string` | ✅ | Dimension unit (e.g. `mm`, `in`) |
> > > 
> > > 
> > > > ##### `vendor` schema
> > > > 
> > > > | Field | Type | Required | Description |
> > > > |:------|:-----|:--------:|:------------|
> > > > | **id** | `string` | ✅ | Vendor ID (`UUID`) |
> > > > | **sku** | `string` | ✅ | Vendor `SKU` |
> > > > | **store** | `string` | ✅ | Vendor name |
> > > > | **name** | `string` | ✅ | Listing name |
> > > > | **price** | `currency` | — | Unit price |
> > > > | **discontinued** | `boolean` | — | Listing discontinued flag |
> > > > | **url** | `string` | — | Vendor product `URL` |
> > > > 
> > > > > ##### `currency` schema
> > > > > 
> > > > > | Field | Type | Required | Description |
> > > > > |:------|:-----|:--------:|:------------|
> > > > > | **value** | `integer` | ✅ | Currency value (minor units) |
> > > > > | **unit** | `string` | ✅ | Currency code (e.g. `USD`, `CAD`) |
> > > >
> > >
> > 
> > 
> > > ##### `image` schema
> > > 
> > > | Field | Type | Required | Description |
> > > |:------|:-----|:--------:|:------------|
> > > | **id** | `string` | ✅ | Image ID (`UUID`) |
> > > | **url** | `string` | ✅ | Presigned `URL` for normalized image (`PNG`) |
> >
>

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
> 
> > ##### `product` schema
> > 
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **id** | `string` | ✅ | Product ID (`UUID`) |
> > | **name** | `name` | ✅ | Product name fields (`brand`, `series`, `model`) |
> > | **category** | map[`string`→`string`] | ✅ | Product attribute map (`key`→`value`) |
> > | **formats** | array[`format`] | ✅ | Available formats |
> > | **images** | array[`image`] | ✅ | Normalized product images |
> > 
> > > ##### `name` schema
> > > 
> > > | Field | Type | Required | Description |
> > > |:------|:-----|:--------:|:------------|
> > > | **brand** | `string` | — | Brand name |
> > > | **series** | `string` | — | Series name |
> > > | **model** | `string` | — | Model name |
> > 
> > 
> > > ##### `format` schema
> > > 
> > > | Field | Type | Required | Description |
> > > |:------|:-----|:--------:|:------------|
> > > | **id** | `string` | ✅ | Format ID (`UUID`) |
> > > | **aspect** | `string` | ✅ | Aspect ratio (`length`:`width`) |
> > > | **length** | `dimension` | — | Longest dimension |
> > > | **width** | `dimension` | — | Shortest dimension |
> > > | **thickness** | `dimension` | — | Thickness dimension |
> > > | **vendors** | array[`vendor`] | — | Vendor listings for this format |
> > > 
> > > > ##### `dimension` schema
> > > > 
> > > > | Field | Type | Required | Description |
> > > > |:------|:-----|:--------:|:------------|
> > > > | **value** | `integer` | ✅ | Dimension value |
> > > > | **unit** | `string` | ✅ | Dimension unit (e.g. `mm`, `in`) |
> > > 
> > > 
> > > > ##### `vendor` schema
> > > > 
> > > > | Field | Type | Required | Description |
> > > > |:------|:-----|:--------:|:------------|
> > > > | **id** | `string` | ✅ | Vendor ID (`UUID`) |
> > > > | **sku** | `string` | ✅ | Vendor `SKU` |
> > > > | **store** | `string` | ✅ | Vendor name |
> > > > | **name** | `string` | ✅ | Listing name |
> > > > | **price** | `currency` | — | Unit price |
> > > > | **discontinued** | `boolean` | — | Listing discontinued flag |
> > > > | **url** | `string` | — | Vendor product `URL` |
> > > > 
> > > > > ##### `currency` schema
> > > > > 
> > > > > | Field | Type | Required | Description |
> > > > > |:------|:-----|:--------:|:------------|
> > > > > | **value** | `integer` | ✅ | Currency value (minor units) |
> > > > > | **unit** | `string` | ✅ | Currency code (e.g. `USD`, `CAD`) |
> > > >
> > >
> > 
> > 
> > > ##### `image` schema
> > > 
> > > | Field | Type | Required | Description |
> > > |:------|:-----|:--------:|:------------|
> > > | **id** | `string` | ✅ | Image ID (`UUID`) |
> > > | **url** | `string` | ✅ | Presigned `URL` for normalized image (`PNG`) |
> >
>

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
> 
> > ##### `product` schema
> > 
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **id** | `string` | ✅ | Product ID (`UUID`) |
> > | **name** | `name` | ✅ | Product name fields (`brand`, `series`, `model`) |
> > | **category** | map[`string`→`string`] | ✅ | Product attribute map (`key`→`value`) |
> > | **formats** | array[`format`] | ✅ | Available formats |
> > | **images** | array[`image`] | ✅ | Normalized product images |
> > 
> > > ##### `name` schema
> > > 
> > > | Field | Type | Required | Description |
> > > |:------|:-----|:--------:|:------------|
> > > | **brand** | `string` | — | Brand name |
> > > | **series** | `string` | — | Series name |
> > > | **model** | `string` | — | Model name |
> > 
> > 
> > > ##### `format` schema
> > > 
> > > | Field | Type | Required | Description |
> > > |:------|:-----|:--------:|:------------|
> > > | **id** | `string` | ✅ | Format ID (`UUID`) |
> > > | **aspect** | `string` | ✅ | Aspect ratio (`length`:`width`) |
> > > | **length** | `dimension` | — | Longest dimension |
> > > | **width** | `dimension` | — | Shortest dimension |
> > > | **thickness** | `dimension` | — | Thickness dimension |
> > > | **vendors** | array[`vendor`] | — | Vendor listings for this format |
> > > 
> > > > ##### `dimension` schema
> > > > 
> > > > | Field | Type | Required | Description |
> > > > |:------|:-----|:--------:|:------------|
> > > > | **value** | `integer` | ✅ | Dimension value |
> > > > | **unit** | `string` | ✅ | Dimension unit (e.g. `mm`, `in`) |
> > > 
> > > 
> > > > ##### `vendor` schema
> > > > 
> > > > | Field | Type | Required | Description |
> > > > |:------|:-----|:--------:|:------------|
> > > > | **id** | `string` | ✅ | Vendor ID (`UUID`) |
> > > > | **sku** | `string` | ✅ | Vendor `SKU` |
> > > > | **store** | `string` | ✅ | Vendor name |
> > > > | **name** | `string` | ✅ | Listing name |
> > > > | **price** | `currency` | — | Unit price |
> > > > | **discontinued** | `boolean` | — | Listing discontinued flag |
> > > > | **url** | `string` | — | Vendor product `URL` |
> > > > 
> > > > > ##### `currency` schema
> > > > > 
> > > > > | Field | Type | Required | Description |
> > > > > |:------|:-----|:--------:|:------------|
> > > > > | **value** | `integer` | ✅ | Currency value (minor units) |
> > > > > | **unit** | `string` | ✅ | Currency code (e.g. `USD`, `CAD`) |
> > > >
> > >
> > 
> > 
> > > ##### `image` schema
> > > 
> > > | Field | Type | Required | Description |
> > > |:------|:-----|:--------:|:------------|
> > > | **id** | `string` | ✅ | Image ID (`UUID`) |
> > > | **url** | `string` | ✅ | Presigned `URL` for normalized image (`PNG`) |
> >
>

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
