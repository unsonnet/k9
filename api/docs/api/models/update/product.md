# ``product``

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| name | ``name`` | optional | Product name fields (`brand`, `series`, `model`) |
| category | map[`string`→`string` \| `null`] | optional | Product attribute map (`key`→`value`) |

# ``name``

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| brand | `string` \| `null` | optional | Brand name |
| series | `string` \| `null` | optional | Series name |
| model | `string` \| `null` | optional | Model name |

# ``format``

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| aspect | `string` | optional | Aspect ratio (`length`:`width`) |
| length | ``dimension`` \| `null` | optional | Longest dimension |
| width | ``dimension`` \| `null` | optional | Shortest dimension |
| thickness | ``dimension`` \| `null` | optional | Thickness dimension |

# ``dimension``

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| value | `integer` | required | Dimension value |
| unit | `string` | required | Dimension unit (e.g. `mm`, `in`) |

# ``vendor``

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| sku | `string` | optional | Vendor `SKU` |
| store | `string` | optional | Vendor name |
| name | `string` | optional | Listing name |
| price | ``currency`` \| `null` | optional | Unit price |
| discontinued | `boolean` \| `null` | optional | Listing discontinued flag |
| url | `string` \| `null` | optional | Vendor product `URL` |

# ``currency``

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| value | `integer` | required | Currency value (minor units) |
| unit | `string` | required | Currency code (e.g. `USD`, `CAD`) |

# ``image``

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| mask | `string` | optional | `boolean` mask matrix (`Base64`) |
| hom | `string` | optional | `float32[3×3]` homography matrix (`Base64`) |