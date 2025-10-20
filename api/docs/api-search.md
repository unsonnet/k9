# API Reference

# Table of Contents

- [Search API](#search-api)
  - [POST /search](#post-search)


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
> 
> > ##### `name` schema
> > 
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **brand** | `string` | — | Fuzzy filter for brand name |
> > | **series** | `string` | — | Fuzzy filter for series name |
> > | **model** | `string` | — | Fuzzy filter for model name |
> 
> 
> > ##### `format` schema
> > 
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **aspect** | `string` | — | Exact-match filter for aspect ratio |
> > | **length** | `dimension` | — | Range filter for longest dimension |
> > | **width** | `dimension` | — | Range filter for shortest dimension |
> > | **thickness** | `dimension` | — | Range filter for thickness dimension |
> > 
> > > ##### `dimension` schema
> > > 
> > > | Field | Type | Required | Description |
> > > |:------|:-----|:--------:|:------------|
> > > | **min** | `integer` | — | Lower inclusive bound of dimension value |
> > > | **max** | `integer` | — | Upper inclusive bound of dimension value |
> > > | **unit** | `string` | ✅ | Dimension unit (e.g. `mm`, `in`) |
> >
> 
> 
> > ##### `vendor` schema
> > 
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **sku** | `string` | — | Fuzzy filter for vendor `SKU` |
> > | **store** | array[`string`] | — | Exact-match filter for vendor name |
> > | **name** | `string` | — | Fuzzy filter for listing name |
> > | **price** | `currency` | — | Range filter for unit price |
> > | **discontinued** | `boolean` | — | Filter for listing discontinued flag |
> > 
> > > ##### `currency` schema
> > > 
> > > | Field | Type | Required | Description |
> > > |:------|:-----|:--------:|:------------|
> > > | **min** | `integer` | — | Lower inclusive bound of currency value |
> > > | **max** | `integer` | — | Upper inclusive bound of currency value |
> > > | **unit** | `string` | ✅ | Currency code (e.g. `USD`, `CAD`) |
> >
>

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
> 
> > ##### `productSummary` schema
> > 
> > | Field | Type | Required | Description |
> > |:------|:-----|:--------:|:------------|
> > | **id** | `string` | ✅ | Product ID (`UUID`) |
> > | **name** | `name` | ✅ | Product name fields (`brand`, `series`, `model`) |
> > | **image** | `image` | ✅ | Primary product image |
> > | **match** | `integer` | ✅ | Similarity score from `0` to `100` percent |
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
> > > ##### `image` schema
> > > 
> > > | Field | Type | Required | Description |
> > > |:------|:-----|:--------:|:------------|
> > > | **id** | `string` | ✅ | Image ID (`UUID`) |
> > > | **url** | `string` | ✅ | Presigned `URL` for normalized image (`PNG`) |
> >
>

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
