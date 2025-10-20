<!-- import read.product as product -->

# ``reportSummary``

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| id | `string` | required | Report ID (`UUID`) |
| author | `string` | required | User ID (`UUID`) |
| title | `string` | required | Report title |
| date | `string` | required | Creation timestamp (`UTC`) |
| reference | ``product.productSummary`` | required | Reference product summary |

# ``report``

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| id | `string` | required | Report ID (`UUID`) |
| author | `string` | required | User ID (`UUID`) |
| title | `string` | required | Report title |
| date | `string` | required | Creation timestamp (`UTC`) |
| reference | ``product.product`` | required | Reference product |
| favorites | array[``product.product``] | optional | Favorited products |
