# Authentication Flow Documentation

## Overview

The API supports two authentication methods:
1. **Direct Email/Password Authentication** - Traditional login using AWS Cognito User Pools
2. **OAuth Authentication** - Social login using AWS Cognito hosted UI

## Authentication Methods

### 1. Email/Password Authentication

**Registration Flow:**
1. `POST /auth/register` - Register new user
2. User receives email verification (if enabled)
3. `POST /auth/login` - Login with credentials
4. Receive access and refresh tokens

**Login Flow:**
1. `POST /auth/login` - Authenticate with email/password
2. Receive access token (JWT) and refresh token
3. Use access token in `Authorization: Bearer <token>` header

**Token Refresh:**
1. `POST /auth/refresh` - Exchange refresh token for new access token

**Password Reset:**
1. `POST /auth/forgot-password` - Request password reset
2. User receives email with confirmation code
3. `POST /auth/confirm-reset` - Confirm reset with code and new password

### 2. OAuth Authentication (Cognito Hosted UI)

**OAuth Flow:**
1. `GET /auth/cognito/authorize` - Redirect to Cognito hosted UI
2. User authenticates with social provider (Google, Facebook, etc.)
3. Cognito redirects back with authorization code
4. `POST /auth/cognito/callback` - Exchange code for tokens
5. Receive access and refresh tokens

## User Management

### CRUD Operations

**List Users** (Admin only):
- `GET /user` - Paginated list of all users

**Create User** (Admin only):
- `POST /user` - Create new user account

**Read User**:
- `GET /user/{uid}` - Get user details (own profile or admin)

**Update User**:
- `PATCH /user/{uid}` - Update user details (own profile or admin)
- `PATCH /user/{uid}/password` - Update password

**Delete User**:
- `DELETE /user/{uid}` - Delete user account (own account or admin)

### Profile Management

**Current User Profile**:
- `GET /auth/me` - Get current authenticated user profile

## Authorization Levels

### Roles
- `user` - Standard user permissions
- `admin` - Administrator permissions

### Permissions
- **Users** can access and modify their own profile
- **Administrators** can access and modify any user profile
- **Administrators** can list all users and create new accounts

## Error Handling

Standard HTTP status codes are used:
- `200` - Success
- `201` - Created
- `204` - No Content (successful deletion)
- `400` - Bad Request (invalid payload)
- `401` - Unauthorized (missing/invalid token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found (resource doesn't exist)
- `409` - Conflict (resource already exists)
- `423` - Locked (account locked/requires verification)
- `500` - Internal Server Error

## Security Considerations

- All endpoints except registration, login, and password reset require authentication
- JWT tokens should be stored securely on the client side
- Refresh tokens should be used to obtain new access tokens
- Passwords must meet minimum complexity requirements (8+ characters)
- Rate limiting should be implemented for authentication endpoints
- CSRF protection is provided via state parameter in OAuth flow
