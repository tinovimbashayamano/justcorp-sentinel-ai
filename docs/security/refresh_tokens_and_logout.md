# Refresh Tokens and Logout

## Objective

This document describes refresh-token rotation and logout for JustCorp Sentinel AI.

## Purpose

Access tokens are intentionally short-lived. Refresh tokens allow users to obtain new access tokens without repeatedly submitting credentials.

## Token Types

| Token | Purpose | Lifetime |
|---|---|---|
| Access token | Authorizes API requests | Short |
| Refresh token | Obtains a new token pair | Longer |

## Refresh Token Storage

Raw refresh tokens are returned only to the client.

PostgreSQL stores only a SHA-256 token hash.

## Database Table

Refresh tokens are stored in:

- `refresh_tokens`

## Refresh Flow

```text
Login
    |
Access token issued
    |
Refresh token issued
    |
Refresh token submitted
    |
Token hash located
    |
Expiration and revocation checked
    |
Old token revoked
    |
New access token issued
    |
New refresh token issued
```

## Logout Flow

```text
Refresh token submitted
    |
Token located
    |
Token marked revoked
    |
Future refresh rejected
```

## Endpoints

### Refresh Tokens

`POST /api/v1/auth/refresh`

### Logout

`POST /api/v1/auth/logout`

## Security Decisions

- Raw refresh tokens are not stored.
- Refresh tokens are rotated after use.
- Used tokens are revoked.
- Logged-out tokens cannot refresh.
- Expired tokens are rejected.
- Inactive users cannot refresh.
- Logout is idempotent.

## Limitation

Revoking a refresh token does not immediately invalidate an already-issued access token. The access token remains valid until its short expiration period ends.

## Conclusion

Refresh-token rotation improves user experience while preserving revocation and session-control capabilities.
