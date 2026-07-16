# Authentication API

## Objective

This document describes the authentication endpoints for JustCorp Sentinel AI.

## Purpose

The authentication API allows users to register, log in, receive a JWT access token, and retrieve their current authenticated profile.

## Endpoints

### Register User

```http
POST /api/v1/auth/register
```

Registration accepts:

- `username`
- `email`
- `password`
- `full_name`

Publicly registered users receive the default `viewer` role.

### Login

```http
POST /api/auth/login
```

The login endpoint accepts OAuth2 form fields:

- `username`
- `password`

The `username` field may contain either a username or email address.

Successful login returns:

- `access_token`
- `token_type`
- `expires_in_seconds`

### Current User

```http
GET /api/auth/me
```

This endpoint requires:

```http
Authorization: Bearer <access_token>
```

It returns the authenticated user's safe profile fields.

## Authentication Flow

```text
Register
    |
Password validated
    |
Argon2 hash stored
    |
Login
    |
Credentials verified
    |
JWT issued
    |
Bearer token sent
    |
JWT validated
    |
User loaded from PostgreSQL
    |
Current user returned
```

## Security Behaviour

- Duplicate usernames return `409 Conflict`.
- Duplicate emails return `409 Conflict`.
- Invalid credentials return `401 Unauthorized`.
- Missing or invalid access tokens return `401 Unauthorized`.
- Inactive accounts cannot authenticate.
- Password hashes are never returned.
- Public users cannot choose privileged roles.

## Swagger Authentication

FastAPI exposes an **Authorize** button in `/docs`.

The login endpoint follows the OAuth2 password flow expected by the Swagger interface.

## Conclusion

These endpoints establish user identity and JWT issuance. Existing fraud endpoints will be protected and assigned role permissions in the next stage.
