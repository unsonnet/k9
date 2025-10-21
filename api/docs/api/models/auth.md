# ``forgot``

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| username | `string` | required | User name |

# ``credentials``

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| username | `string` | required | User name |
| password | `string` | required | User password |

# ``refresh``

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| username | `string` | required | User name |
| refreshToken | `string` | required | JWT refresh token |

# ``challenge``

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| username | `string` | required | User name |
| challenge | `string` | required | Challenge type (`NEW_PASSWORD_REQUIRED`) |
| session | `string` | required | Session token for challenge response |

# ``reset``

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| username | `string` | required | User name |
| session | `string` | required | Session token |
| newPassword | `string` | required | New password |

# ``session``

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| user | `string` | required | User ID (`UUID`) |
| accessToken | `string` | required | JWT access token |
| refreshToken | `string` | required | JWT refresh token |
| expiresIn | `integer` | required | Access token expiry (`seconds`) |
