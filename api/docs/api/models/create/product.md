# ``product``

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| name | ``name`` | required | Product name fields (`brand`, `series`, `model`) |
| category | map[`string`→`string`] | required | Product attribute map (`key`→`value`) |

# ``name``

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| brand | `string` | optional | Brand name |
| series | `string` | optional | Series name |
| model | `string` | optional | Model name |

# ``format``

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| aspect | `string` | required | Aspect ratio (`length`:`width`) |
| length | ``dimension`` | optional | Longest dimension |
| width | ``dimension`` | optional | Shortest dimension |
| thickness | ``dimension`` | optional | Thickness dimension |

# ``dimension``

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| value | `integer` | required | Dimension value |
| unit | `string` | required | Dimension unit (e.g. `mm`, `in`) |

# ``vendor``

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
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
| image | `binary` | required | `JPEG` image data |
| mask | `string` | required | `boolean` mask matrix (`Base64`) |
| hom | `string` | required | `float32[3×3]` homography matrix (`Base64`) |