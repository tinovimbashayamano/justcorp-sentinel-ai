# Admin User Management

## Objective

This document describes the administrator-only user management API for JustCorp Sentinel AI.

## Purpose

The admin API allows authorized administrators to inspect users, assign roles, and activate or deactivate accounts without directly editing PostgreSQL.

## Authorization Requirement

All endpoints under:

- `/api/v1/admin/users`

require an authenticated user with the `admin` role.

## Endpoints

### List Users

```http
GET /api/v1/admin/users
```

Supports:

- `limit`
- `offset`

### Get One User

```http
GET /api/v1/admin/users/{user_id}
```

### Change User Role

```http
PATCH /api/v1/admin/users/{user_id}/role
```

Accepted roles:

- `admin`
- `fraud_analyst`
- `auditor`
- `viewer`

### Change User Status

```http
PATCH /api/v1/admin/users/{user_id}/status
```

Used to activate or deactivate an account.

## Security Rules

- Public registration always assigns `viewer`.
- Only admins may change roles.
- Only admins may activate or deactivate accounts.
- Administrators cannot remove their own admin role.
- Administrators cannot deactivate their own account.
- Password hashes are never returned.
- User-management endpoints require JWT authentication.

## Bootstrap Administrator

The first administrator is assigned directly in PostgreSQL during initial setup.

After bootstrap, normal role changes should use the admin API.

## Status Codes

| Situation | Response |
| --- | --- |
| Missing token | 401 Unauthorized |
| Non-admin user | 403 Forbidden |
| User not found | 404 Not Found |
| Unsafe self-change | 400 Bad Request |
| Successful update | 200 OK |

## Conclusion

The admin user-management API replaces routine direct database editing with validated, authenticated, and role-protected platform operations.
