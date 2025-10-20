<!-- import read.product as product -->

# ``productSummary``

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| id | `string` | required | Product ID (`UUID`) |
| name | ``product.name`` | required | Product name fields (`brand`, `series`, `model`) |
| image | ``product.image`` | required | Primary product image |
| match | `integer` | required | Similarity score from `0` to `100` percent |