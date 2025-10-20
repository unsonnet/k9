# ``productSummary``

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| id | `string` | required | Product ID (`UUID`) |
| name | ``name`` | required | Product name fields (`brand`, `series`, `model`) |
| image | ``image`` | required | Primary product image |

# ``product``

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| id | `string` | required | Product ID (`UUID`) |
| name | ``name`` | required | Product name fields (`brand`, `series`, `model`) |
| category | map[`string`→`string`] | required | Product attribute map (`key`→`value`) |
| formats | array[``format``] | required | Available formats |
| images | array[``image``] | required | Normalized product images |

# ``name``

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| brand | `string` | optional | Brand name |
| series | `string` | optional | Series name |
| model | `string` | optional | Model name |

# ``format``

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| id | `string` | required | Format ID (`UUID`) |
| aspect | `string` | required | Aspect ratio (`length`:`width`) |
| length | ``dimension`` | optional | Longest dimension |
| width | ``dimension`` | optional | Shortest dimension |
| thickness | ``dimension`` | optional | Thickness dimension |
| vendors | array[``vendor``] | optional | Vendor listings for this format |

# ``dimension``

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| value | `integer` | required | Dimension value |
| unit | `string` | required | Dimension unit (e.g. `mm`, `in`) |

# ``vendor``

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| id | `string` | required | Vendor ID (`UUID`) |
| sku | `string` | required | Vendor `SKU` |
| store | `string` | required | Vendor name |
| name | `string` | required | Listing name |
| price | ``currency`` | optional | Unit price |
| discontinued | `boolean` | optional | Listing discontinued flag |
| url | `string` | optional | Vendor product `URL` |

# ``currency``

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| value | `integer` | required | Currency value (minor units) |
| unit | `string` | required | Currency code (e.g. `USD`, `CAD`) |

# ``image``

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| id | `string` | required | Image ID (`UUID`) |
| url | `string` | required | Presigned `URL` for normalized image (`PNG`) |