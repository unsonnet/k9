# ``credentials``

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| email | `string` | required | User email |
| password | `string` | required | User password |

# ``session``

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| user | `string` | required | User ID (`UUID`) |
| accessToken | `string` | required | JWT access token |
| refreshToken | `string` | required | JWT refresh token |
| expiresIn | `integer` | required | Access token expiry (`seconds`) |

# ``refresh``

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| refreshToken | `string` | required | JWT refresh token |

# ``forgot``

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| email | `string` | required | User email |

# ``challenge``

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| user | `string` | required | User ID (`UUID`) |
| challenge | `string` | required | Challenge type (`NEW_PASSWORD_REQUIRED`) |
| session | `string` | required | Session token for challenge response |

# ``reset``

| Field | Type | Required | Description |
|-------|------|-----------|--------------|
| user | `string` | required | User ID (`UUID`) |
| session | `string` | required | Session token |
| newPassword | `string` | required | New password |
