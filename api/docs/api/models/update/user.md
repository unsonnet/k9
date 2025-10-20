# ``profile``

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| username | `string` | optional | Display name |
| email | `string` | optional | Primary email |
| role | `string` | optional | Permission level (only for administrator role) |
| preferences | map[`string`→`string` \| `null`] | optional | Dashboard settings |

# ``password``

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| currentPassword | `string` | required | Current password |
| newPassword | `string` | required | New password (min 8 chars) |
