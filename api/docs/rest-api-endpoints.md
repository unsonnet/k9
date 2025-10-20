# Product API

## POST `/product`

Creates a new product

### Request

<!-- Schema Begin -->
#### Headers

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| **Authorization** | string | required | JWT used for authentication |
<!-- Schema End -->

<!-- Schema Begin -->
#### Body (`application/json`)

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| **name** | `name` | required | Structured name fields |
| **category** | map[string→string] | required | Mapping of product attributes |
| **formats** | array[`format`] | required | List of available size configurations |
| **images** | array[string] | required | List of image IDs (`UUID`) |

#### `name`

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| **brand** | string | optional | Product brand |
| **series** | string | optional | Product series |
| **model** | string | optional | Product model |

#### `format`

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| **length** | `quantity` | required | Longest dimension (same unit as `width`) |
| **width** | `quantity` | required | Shortest dimension (same unit as `length`) |
| **thickness** | `quantity` | optional | Thickness dimension (unit required if provided) |
| **vendors** | array[`vendor`] | optional | List of vendor listings |

#### `vendor`

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| **sku** | string | required | Vendor product SKU |
| **store** | string | required | Vendor name |
| **name** | string | required | Listing name |
| **price** | `quantity` | optional | Unit price |
| **discontinued** | boolean | optional | Product availability |
| **url** | string | required | Vendor product page URL |

#### `quantity`

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| **value** | number | required | Numeric value (dimensionless if `unit` omitted) |
| **unit** | string | optional | Unit symbol (e.g. `mm`, `in`, `$`) |
<!-- Schema End -->

### Response 200 OK

<!-- Schema Begin -->
#### Body (`application/json`)

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| **id** | string | required | Product ID (`UUID`) |
| **name** | `name` | required | Structured name fields |
| **category** | map[string→string] | required | Mapping of product attributes |
| **formats** | array[`format`] | required | List of available size configurations |
| **images** | array[`image`] | required | List of product images |

#### `name`

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| **brand** | string | optional | Product brand |
| **series** | string | optional | Product series |
| **model** | string | optional | Product model |

#### `format`

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| **length** | `quantity` | required | Longest dimension (same unit as `width`) |
| **width** | `quantity` | required | Shortest dimension (same unit as `length`) |
| **thickness** | `quantity` | optional | Thickness dimension (unit required if provided) |
| **vendors** | array[`vendor`] | optional | List of vendor listings |

#### `vendor`

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| **sku** | string | required | Vendor product SKU |
| **store** | string | required | Vendor name |
| **name** | string | required | Listing name |
| **price** | `quantity` | optional | Unit price |
| **discontinued** | boolean | optional | Product availability |
| **url** | string | required | Vendor product page URL |

#### `quantity`

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| **value** | number | required | Numeric value (dimensionless if `unit` omitted) |
| **unit** | string | optional | Unit symbol (e.g. `mm`, `in`, `$`) |

#### `image`

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| **id** | string | required | Image ID (`UUID`) |
| **url** | string | required | Presigned S3 URL for the image |
| **hom** | string | required | Base64-encoded `float32[3×3]` homography matrix |
<!-- Schema End -->

### Response 400 Bad Request

Returned when the request body is malformed (`InvalidRequest`)

### Response 401 Unauthorized

Returned when authentication credentials are missing or invalid (`Unauthorized`)

### Response 404 Not Found

Returned when one or more referenced images do not exist (`NotFound`)

### Response 500 Internal Server Error

Returned when an unexpected error occurs (`InternalServerError`)

---

## GET `/product/{id}`

Retrieves detailed data for a product

### Request

<!-- Schema Begin -->
#### Headers

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| **Authorization** | string | required | JWT used for authentication |
<!-- Schema End -->

<!-- Schema Begin -->
#### Path Parameters

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| **id** | string | required | Product ID (`UUID`) |
<!-- Schema End -->

### Response 200 OK

<!-- Schema Begin -->
#### Body (`application/json`)

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| **id** | string | required | Product ID (`UUID`) |
| **name** | `name` | required | Structured name fields |
| **category** | map[string→string] | required | Mapping of product attributes |
| **formats** | array[`format`] | required | List of available size configurations |
| **images** | array[`image`] | required | List of product images |

#### `name`

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| **brand** | string | optional | Product brand |
| **series** | string | optional | Product series |
| **model** | string | optional | Product model |

#### `format`

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| **length** | `quantity` | required | Longest dimension (same unit as `width`) |
| **width** | `quantity` | required | Shortest dimension (same unit as `length`) |
| **thickness** | `quantity` | optional | Thickness dimension (unit required if provided) |
| **vendors** | array[`vendor`] | optional | List of vendor listings |

#### `vendor`

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| **sku** | string | required | Vendor product SKU |
| **store** | string | required | Vendor name |
| **name** | string | required | Listing name |
| **price** | `quantity` | optional | Unit price |
| **discontinued** | boolean | optional | Product availability |
| **url** | string | required | Vendor product page URL |

#### `quantity`

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| **value** | number | required | Numeric value (dimensionless if `unit` omitted) |
| **unit** | string | optional | Unit symbol (e.g. `mm`, `in`, `$`) |

#### `image`

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| **id** | string | required | Image ID (`UUID`) |
| **url** | string | required | Presigned S3 URL for the image |
| **hom** | string | required | Base64-encoded `float32[3×3]` homography matrix |
<!-- Schema End -->

### Response 401 Unauthorized

Returned when authentication credentials are missing or invalid (`Unauthorized`)

### Response 403 Forbidden

Returned when the user lacks permission to access the product (`Forbidden`)

### Response 404 Not Found

Returned when the product does not exist (`NotFound`)

### Response 500 Internal Server Error

Returned when an unexpected error occurs (`InternalServerError`)

---

## PATCH `/product/{id}`

Updates an existing product  
Only the fields provided in the request body are updated. Unspecified fields remain unchanged

### Request

<!-- Schema Begin -->
#### Headers

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| **Authorization** | string | required | JWT used for authentication |
<!-- Schema End -->

<!-- Schema Begin -->
#### Path Parameters

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| **id** | string | required | Product ID (`UUID`) |
<!-- Schema End -->

<!-- Schema Begin -->
#### Body (`application/json`)
<!-- TODO -->
<!-- Schema End -->

### Response 200 OK

<!-- Schema Begin -->
#### Body (`application/json`)

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| **id** | string | required | Product ID (`UUID`) |
| **name** | `name` | required | Structured name fields |
| **category** | map[string→string] | required | Mapping of product attributes |
| **formats** | array[`format`] | required | List of available size configurations |
| **images** | array[`image`] | required | List of product images |

#### `name`

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| **brand** | string | optional | Product brand |
| **series** | string | optional | Product series |
| **model** | string | optional | Product model |

#### `format`

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| **length** | `quantity` | required | Longest dimension (same unit as `width`) |
| **width** | `quantity` | required | Shortest dimension (same unit as `length`) |
| **thickness** | `quantity` | optional | Thickness dimension (unit required if provided) |
| **vendors** | array[`vendor`] | optional | List of vendor listings |

#### `vendor`

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| **sku** | string | required | Vendor product SKU |
| **store** | string | required | Vendor name |
| **name** | string | required | Listing name |
| **price** | `quantity` | optional | Unit price |
| **discontinued** | boolean | optional | Product availability |
| **url** | string | required | Vendor product page URL |

#### `quantity`

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| **value** | number | required | Numeric value (dimensionless if `unit` omitted) |
| **unit** | string | optional | Unit symbol (e.g. `mm`, `in`, `$`) |

#### `image`

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| **id** | string | required | Image ID (`UUID`) |
| **url** | string | required | Presigned S3 URL for the image |
| **hom** | string | required | Base64-encoded `float32[3×3]` homography matrix |
<!-- Schema End -->

### Response 400 Bad Request

Returned when the request body is malformed (`InvalidRequest`)

### Response 401 Unauthorized

Returned when authentication credentials are missing or invalid (`Unauthorized`)

### Response 403 Forbidden

Returned when the user lacks permission to modify the product (`Forbidden`)

### Response 404 Not Found

Returned when the product or referenced images do not exist (`NotFound`)

### Response 500 Internal Server Error

Returned when an unexpected error occurs (`InternalServerError`)

---

## POST `/product/image`

Uploads a `.png` image and its homography matrix for use in products

### Request

<!-- Schema Begin -->
#### Headers

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| **Authorization** | string | required | JWT used for authentication |
| **Content-Type** | string | required | Must be `multipart/form-data` |
<!-- Schema End -->

<!-- Schema Begin -->
#### Body (`multipart/form-data`)

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| **file** | binary (`.png`) | required | PNG image with alpha channel encoding a binary mask |
| **hom** | string | required | Base64-encoded `float32[3×3]` homography matrix |
<!-- Schema End -->

### Response 200 OK

<!-- Schema Begin -->
#### Body (`application/json`)

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| **id** | string | required | Image ID (`UUID`) |
| **url** | string | required | Presigned S3 URL for the image |
| **hom** | string | required | Base64-encoded `float32[3×3]` homography matrix |
<!-- Schema End -->

### Response 400 Bad Request

Returned when the image or homography data is invalid (`InvalidImageFormat`, `InvalidHomography`)

### Response 401 Unauthorized

Returned when authentication credentials are missing or invalid (`Unauthorized`)

### Response 500 Internal Server Error

Returned when an unexpected error occurs (`InternalServerError`)

---

## PATCH `/product/image/{id}`

Updates metadata for an uploaded product image

### Request

<!-- Schema Begin -->
#### Headers

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| **Authorization** | string | required | JWT used for authentication |
<!-- Schema End -->

<!-- Schema Begin -->
#### Path Parameters

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| **id** | string | required | Image ID (`UUID`) |
<!-- Schema End -->

<!-- Schema Begin -->
#### Body (`application/json`)
<!-- TODO -->
<!-- Schema End -->

### Response 200 OK

<!-- Schema Begin -->
#### Body (`application/json`)

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| **id** | string | required | Image ID (`UUID`) |
| **url** | string | required | Presigned S3 URL for the image |
| **hom** | string | required | Base64-encoded `float32[3×3]` homography matrix |
<!-- Schema End -->

### Response 400 Bad Request

Returned when the request body is malformed or references invalid data (`InvalidRequest`, `InvalidHomography`)

### Response 401 Unauthorized

Returned when authentication credentials are missing or invalid (`Unauthorized`)

### Response 403 Forbidden

Returned when the user lacks permission to modify the image (`Forbidden`)

### Response 404 Not Found

Returned when the image does not exist (`NotFound`)

### Response 500 Internal Server Error

Returned when an unexpected error occurs (`InternalServerError`)

---

# Report API

## GET `/report`

Retrieves a paginated list of reports accessible to the authenticated user

### Request

<!-- Schema Begin -->
#### Headers

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| **Authorization** | string | required | JWT used for authentication |
<!-- Schema End -->

<!-- Schema Begin -->
#### Query Parameters

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| **limit** | integer | optional | Maximum number of reports to return per page (default: `25`) |
| **nextToken** | string | optional | Base64-encoded pagination cursor |
<!-- Schema End -->

### Response 200 OK

<!-- Schema Begin -->
#### Body (`application/json`)

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| **total** | integer | required | Total number of accessible reports |
| **nextToken** | string | optional | Base64-encoded pagination cursor for the next page |
| **reports** | array[`report`] | required | List of report summaries |

#### `report`

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| **id** | string | required | Report ID (`UUID`) |
| **author** | string | required | Author's username |
| **title** | string | required | Report title |
| **date** | string | required | UTC timestamp when created |
| **reference** | string | required | Presigned S3 URL to the reference image |
<!-- Schema End -->

### Response 401 Unauthorized

Returned when authentication credentials are missing or invalid (`Unauthorized`)

### Response 500 Internal Server Error

Returned when an unexpected error occurs (`InternalServerError`)

---

## GET `/report/{id}`

Retrieves detailed data for a report

### Request

<!-- Schema Begin -->
#### Headers

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| **Authorization** | string | required | JWT used for authentication |
<!-- Schema End -->

<!-- Schema Begin -->
#### Path Parameters

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| **id** | string | required | Report ID (`UUID`) |
<!-- Schema End -->

### Response 200 OK

<!-- Schema Begin -->
#### Body (`application/json`)

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| **id** | string | required | Report ID (`UUID`) |
| **author** | string | required | Author's username |
| **title** | string | required | Report title |
| **date** | string | required | UTC timestamp when created |
| **reference** | `product` | required | Reference product analyzed in the report |
| **favorites** | array[`product`] | required | Products marked as favorites |

#### `product`

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| **id** | string | required | Product ID (`UUID`) |
| **name** | `name` | required | Structured name fields |
| **category** | map[string→string] | required | Mapping of product attributes |
| **formats** | array[`format`] | required | List of available size configurations |
| **images** | array[`image`] | required | List of product images |

#### `name`

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| **brand** | string | optional | Product brand |
| **series** | string | optional | Product series |
| **model** | string | optional | Product model |

#### `format`

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| **length** | `quantity` | required | Longest dimension (same unit as `width`) |
| **width** | `quantity` | required | Shortest dimension (same unit as `length`) |
| **thickness** | `quantity` | optional | Thickness dimension (unit required if provided) |
| **vendors** | array[`vendor`] | optional | List of vendor listings |

#### `vendor`

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| **sku** | string | required | Vendor product SKU |
| **store** | string | required | Vendor name |
| **name** | string | required | Listing name |
| **price** | `quantity` | optional | Unit price |
| **discontinued** | boolean | optional | Product availability |
| **url** | string | required | Vendor product page URL |

#### `quantity`

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| **value** | number | required | Numeric value (dimensionless if `unit` omitted) |
| **unit** | string | optional | Unit symbol (e.g. `mm`, `in`, `$`) |

#### `image`

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| **id** | string | required | Image ID (`UUID`) |
| **url** | string | required | Presigned S3 URL for the image |
| **hom** | string | required | Base64-encoded `float32[3×3]` homography matrix |
<!-- Schema End -->

### Response 401 Unauthorized

Returned when authentication credentials are missing or invalid (`Unauthorized`)

### Response 403 Forbidden

Returned when the user lacks permission to access the report (`Forbidden`)

### Response 404 Not Found

Returned when the report does not exist (`NotFound`)

### Response 500 Internal Server Error

Returned when an unexpected error occurs (`InternalServerError`)

---

## PATCH `/report/{id}`

Updates an existing report  
Only the fields provided in the request body are updated. Unspecified fields remain unchanged

### Request

<!-- Schema Begin -->
#### Headers

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| **Authorization** | string | required | JWT used for authentication |
<!-- Schema End -->

<!-- Schema Begin -->
#### Path Parameters

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| **id** | string | required | Report ID (`UUID`) |
<!-- Schema End -->

<!-- Schema Begin -->
#### Body (`application/json`)
<!-- TODO -->
<!-- Schema End -->

### Response 200 OK

<!-- Schema Begin -->
#### Body (`application/json`)

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| **id** | string | required | Report ID (`UUID`) |
| **author** | string | required | Author's username |
| **title** | string | required | Report title |
| **date** | string | required | UTC timestamp when created |
| **reference** | `product` | required | Reference product analyzed in the report |
| **favorites** | array[`product`] | required | Products marked as favorites |

#### `product`

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| **id** | string | required | Product ID (`UUID`) |
| **name** | `name` | required | Structured name fields |
| **category** | map[string→string] | required | Mapping of product attributes |
| **formats** | array[`format`] | required | List of available size configurations |
| **images** | array[`image`] | required | List of product images |

#### `name`

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| **brand** | string | optional | Product brand |
| **series** | string | optional | Product series |
| **model** | string | optional | Product model |

#### `format`

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| **length** | `quantity` | required | Longest dimension (same unit as `width`) |
| **width** | `quantity` | required | Shortest dimension (same unit as `length`) |
| **thickness** | `quantity` | optional | Thickness dimension (unit required if provided) |
| **vendors** | array[`vendor`] | optional | List of vendor listings |

#### `vendor`

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| **sku** | string | required | Vendor product SKU |
| **store** | string | required | Vendor name |
| **name** | string | required | Listing name |
| **price** | `quantity` | optional | Unit price |
| **discontinued** | boolean | optional | Product availability |
| **url** | string | required | Vendor product page URL |

#### `quantity`

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| **value** | number | required | Numeric value (dimensionless if `unit` omitted) |
| **unit** | string | optional | Unit symbol (e.g. `mm`, `in`, `$`) |

#### `image`

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| **id** | string | required | Image ID (`UUID`) |
| **url** | string | required | Presigned S3 URL for the image |
| **hom** | string | required | Base64-encoded `float32[3×3]` homography matrix |
<!-- Schema End -->

### Response 400 Bad Request

Returned when the request body is malformed (`InvalidRequest`)

### Response 401 Unauthorized

Returned when authentication credentials are missing or invalid (`Unauthorized`)

### Response 403 Forbidden

Returned when the user lacks permission to modify the report (`Forbidden`)

### Response 404 Not Found

Returned when the report or referenced images do not exist (`NotFound`)

### Response 500 Internal Server Error

Returned when an unexpected error occurs (`InternalServerError`)

---

## GET `/report/{id}/favorites`

Retrieves a paginated list of favorite products in a report

### Request

<!-- Schema Begin -->
#### Headers

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| **Authorization** | string | required | JWT used for authentication |
<!-- Schema End -->

<!-- Schema Begin -->
#### Path Parameters

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| **id** | string | required | Report ID (`UUID`) |
<!-- Schema End -->

<!-- Schema Begin -->
#### Query Parameters

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| **limit** | integer | optional | Maximum number of favorites to return per page (default: `25`) |
| **nextToken** | string | optional | Base64-encoded pagination cursor |
<!-- Schema End -->

### Response 200 OK

<!-- Schema Begin -->
#### Body (`application/json`)

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| **total** | integer | required | Total number of favorite products |
| **nextToken** | string | optional | Base64-encoded pagination cursor for the next page |
| **favorites** | array[`product`] | required | List of favorite product summaries |

#### `product`

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| **id** | string | required | Product ID (`UUID`) |
| **name** | `name` | required | Structured name fields |
| **image** | string | required | Presigned S3 URL for the primary image |

#### `name`

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| **brand** | string | optional | Product brand |
| **series** | string | optional | Product series |
| **model** | string | optional | Product model |
<!-- Schema End -->

### Response 401 Unauthorized

Returned when authentication credentials are missing or invalid (`Unauthorized`)

### Response 403 Forbidden

Returned when the user lacks permission to access the report (`Forbidden`)

### Response 404 Not Found

Returned when the report does not exist (`NotFound`)

### Response 500 Internal Server Error

Returned when an unexpected error occurs (`InternalServerError`)

---

## PUT `/report/{id}/favorites`

Updates the favorites list for a report

### Request

<!-- Schema Begin -->
#### Headers

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| **Authorization** | string | required | JWT used for authentication |
<!-- Schema End -->

<!-- Schema Begin -->
#### Path Parameters

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| **id** | string | required | Report ID (`UUID`) |
<!-- Schema End -->

<!-- Schema Begin -->
#### Body (`application/json`)

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| **product** | string | required | Product ID (`UUID`) to modify |
| **favorite** | boolean | required | `true` to add, `false` to remove |
<!-- Schema End -->

### Response 200 OK

<!-- Schema Begin -->
#### Body (`application/json`)

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| **favorites** | array[string] | required | Updated list of product IDs |
<!-- Schema End -->

### Response 400 Bad Request

Returned when the request body is malformed or violates limits (`InvalidRequest`, `FavoritesLimitExceeded`)

### Response 401 Unauthorized

Returned when authentication credentials are missing or invalid (`Unauthorized`)

### Response 403 Forbidden

Returned when the user lacks permission to modify the report (`Forbidden`)

### Response 404 Not Found

Returned when the report or product does not exist (`NotFound`)

### Response 500 Internal Server Error

Returned when an unexpected error occurs (`InternalServerError`)

---

## POST `/report`

Creates a new report

### Request

<!-- Schema Begin -->
#### Headers

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| **Authorization** | string | required | JWT used for authentication |
<!-- Schema End -->

<!-- Schema Begin -->
#### Body (`application/json`)

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| **title** | string | required | Report title |
| **reference** | `product` | required | Reference product analyzed in the report |

#### `product`

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| **category** | map[string→string] | required | Mapping of product attributes |
| **formats** | array[`format`] | required | List of available size configurations |
| **images** | array[string] | required | List of image IDs (`UUID`) |

#### `format`

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| **length** | `quantity` | required | Longest dimension (same unit as `width`) |
| **width** | `quantity` | required | Shortest dimension (same unit as `length`) |
| **thickness** | `quantity` | optional | Thickness dimension (must include unit if provided) |

#### `quantity`

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| **value** | number | required | Numeric value (dimensionless if `unit` omitted) |
| **unit** | string | optional | Unit symbol (e.g. `mm`, `in`) |
<!-- Schema End -->

### Response 200 OK

<!-- Schema Begin -->
#### Body (`application/json`)

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| **id** | string | required | Report ID (`UUID`) |
| **author** | string | required | Author's username |
| **title** | string | required | Report title |
| **date** | string | required | UTC timestamp when created |
| **reference** | string | required | Presigned S3 URL to the reference image |
| **favorites** | array[string] | required | Product IDs marked as favorites |
<!-- Schema End -->

### Response 400 Bad Request

Returned when the request body is malformed (`InvalidRequest`)

### Response 401 Unauthorized

Returned when authentication credentials are missing or invalid (`Unauthorized`)

### Response 404 Not Found

Returned when referenced images do not exist (`NotFound`)

### Response 500 Internal Server Error

Returned when an unexpected error occurs (`InternalServerError`)

---

# Error Responses

These standardized response structures are reused across all endpoints to ensure consistent API error handling

---

## Response 400 Bad Request

Returned when the request cannot be processed due to invalid input, malformed syntax, or logical errors in the body or parameters (`InvalidRequest`)

<!-- Schema Begin -->
#### Body (`application/json`)

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| **error** | string | required | Error code describing the failure (e.g. `InvalidRequest`) |
| **message** | string | required | Human-readable message describing the error and corrective action |
<!-- Schema End -->

---

## Response 401 Unauthorized

Returned when authentication credentials are missing, invalid, or expired (`Unauthorized`)

<!-- Schema Begin -->
#### Body (`application/json`)

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| **error** | string | required | Error code indicating authentication failure (`Unauthorized`) |
| **message** | string | required | Human-readable message describing the authentication error |
<!-- Schema End -->

---

## Response 403 Forbidden

Returned when the user is authenticated but lacks permission to perform the requested action or access the specified resource (`Forbidden`)

<!-- Schema Begin -->
#### Body (`application/json`)

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| **error** | string | required | Error code indicating access denial (`Forbidden`) |
| **message** | string | required | Human-readable message describing why access was denied |
<!-- Schema End -->

---

## Response 404 Not Found

Returned when the requested resource does not exist or is inaccessible to the authenticated user (`NotFound`)

<!-- Schema Begin -->
#### Body (`application/json`)

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| **error** | string | required | Error code indicating the resource was not found (`NotFound`) |
| **message** | string | required | Human-readable message describing what could not be found |
<!-- Schema End -->

---

## Response 500 Internal Server Error

Returned when an unexpected condition prevents the server from fulfilling the request (`InternalServerError`)

<!-- Schema Begin -->
#### Body (`application/json`)

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| **error** | string | required | Error code indicating a server-side failure (`InternalServerError`) |
| **message** | string | required | Human-readable message describing the server error |
<!-- Schema End -->
