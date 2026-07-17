# Password and Session Management

## Objective

This document describes password changes and session revocation in JustCorp Sentinel AI.

## Purpose

Users need a secure method to change compromised or outdated passwords and terminate active refresh-token sessions.

## Endpoints

### Change Password

```http
POST /api/v1/auth/change-password
```

Requires a valid access token.

The request includes:

- `current_password`
- `new_password`

### Logout All Sessions

```http
POST /api/v1/auth/logout-all
```

Requires a valid access token.

This endpoint revokes every active refresh token belonging to the authenticated user.

## Password Change Flow

```text
Authenticated user
    |
Current password verified
    |
New password validated
    |
New Argon2 hash stored
    |
All refresh tokens revoked
    |
User logs in again
```

## Security Rules

- The current password must be correct.
- The new password must meet strength requirements.
- The new password must differ from the current password.
- Plaintext passwords are never stored.
- Password changes revoke all active refresh tokens.
- Users can revoke all refresh sessions explicitly.
- Access tokens remain valid only until their short expiration time.

## Session Revocation

Refresh-token records are retained as revoked records for traceability.

Revoked refresh tokens cannot be used to request new access tokens.

## Error Responses

| Situation | Response |
|---|---|
| Missing access token | 401 Unauthorized |
| Incorrect current password | 400 Bad Request |
| Weak new password | 422 Unprocessable Content |
| Reused current password | 400 Bad Request |
| Successful change | 200 OK |

## Conclusion

Password changes and refresh-session revocation strengthen account security by preventing old credentials and stolen refresh tokens from preserving long-term access.
