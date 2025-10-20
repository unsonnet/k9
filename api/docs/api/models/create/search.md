# ``query``

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| name | ``name`` | optional | Fuzzy filters for product name |
| category | map[`string`→array[`string`]] | optional | Exact-match filters for product attributes |
| format | ``format`` | optional | Exact-match and range filters for product formats |
| vendor | ``vendor`` | optional | Fuzzy and range filters for vendor listings |
| colors | array[`string`] | optional | Vector-similarity filter using image colors (`HEX`) |
| references | array[`string`] | optional | Vector-similarity filter using product IDs (`UUID`) |

# ``name``

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| brand | `string` | optional | Fuzzy filter for brand name |
| series | `string` | optional | Fuzzy filter for series name |
| model | `string` | optional | Fuzzy filter for model name |

# ``format``

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| aspect | `string` | optional | Exact-match filter for aspect ratio |
| length | ``dimension`` | optional | Range filter for longest dimension |
| width | ``dimension`` | optional | Range filter for shortest dimension |
| thickness | ``dimension`` | optional | Range filter for thickness dimension |

# ``dimension``

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| min | `integer` | optional | Lower inclusive bound of dimension value |
| max | `integer` | optional | Upper inclusive bound of dimension value |
| unit | `string` | required | Dimension unit (e.g. `mm`, `in`) |

# ``vendor``

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| sku | `string` | optional | Fuzzy filter for vendor `SKU` |
| store | array[`string`] | optional | Exact-match filter for vendor name |
| name | `string` | optional | Fuzzy filter for listing name |
| price | ``currency`` | optional | Range filter for unit price |
| discontinued | `boolean` | optional | Filter for listing discontinued flag |

# ``currency``

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| min | `integer` | optional | Lower inclusive bound of currency value |
| max | `integer` | optional | Upper inclusive bound of currency value |
| unit | `string` | required | Currency code (e.g. `USD`, `CAD`) |
