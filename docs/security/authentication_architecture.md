# Authentication Architecture

## Objective

This document describes the authentication foundation for JustCorp Sentinel AI.

## Purpose

Authentication protects fraud scoring, fraud records, case reviews, reporting, and administrative functions from unauthorized access.

## Authentication Method

The backend uses signed JSON Web Tokens for API authentication.

## Password Security

Passwords are hashed using Argon2 through `pwdlib`.

Plaintext passwords are never stored in the database or returned through the API.

## User Table

Users are stored in the PostgreSQL `users` table.

| Field | Purpose |
|---|---|
| `id` | Internal user identifier |
| `username` | Unique login name |
| `email` | Unique email address |
| `full_name` | Optional display name |
| `hashed_password` | Argon2 password hash |
| `role` | Authorization role |
| `is_active` | Allows account disabling |
| `created_at` | Account creation timestamp |
| `updated_at` | Last update timestamp |

## Roles

| Role | Purpose |
|---|---|
| `admin` | Full platform administration |
| `fraud_analyst` | Fraud scoring and case investigation |
| `auditor` | Read-only audit access |
| `viewer` | Limited read-only access |

## JWT Claims

The access token contains:

- `sub`
- `role`
- `iat`
- `exp`
- `type`

## Configuration

Authentication configuration is loaded from environment variables:

- `JWT_SECRET_KEY`
- `JWT_ALGORITHM`
- `ACCESS_TOKEN_EXPIRE_MINUTES`

The real secret is stored in `.env`, which is excluded from Git.

## Security Decisions

- Public users cannot choose privileged roles.
- Passwords must meet minimum strength requirements.
- Tokens expire after a configurable period.
- Invalid and expired tokens are rejected.
- Authorization will use the current database role.
- Secrets are not committed to source control.

## Authentication Flow

```text
Registration
    |
Password validation
    |
Argon2 hashing
    |
User stored in PostgreSQL
    |
Login
    |
Password verification
    |
JWT access token issued
    |
Bearer token submitted
    |
Token validated
    |
User loaded from database
    |
Role checked
    |
Protected endpoint executed
```

## Conclusion

This foundation provides the secure password, user, role, token, and configuration components required for the registration, login, and protected-route APIs.
