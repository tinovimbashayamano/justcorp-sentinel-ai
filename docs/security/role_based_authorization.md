# Role-Based Authorization

## Objective

This document describes role-based access control for the JustCorp Sentinel AI fraud API.

## Purpose

Authentication identifies the user. Authorization determines which fraud operations that user may perform.

## Roles

| Role | Purpose |
| --- | --- |
| `admin` | Full platform access |
| `fraud_analyst` | Fraud scoring and investigation work |
| `auditor` | Read-only audit and review access |
| `viewer` | Limited authenticated access |

## Permission Matrix

| Operation | Admin | Fraud Analyst | Auditor | Viewer |
| --- | ---: | ---: | ---: | ---: |
| View model health | Yes | Yes | Yes | Yes |
| Score transaction | Yes | Yes | No | No |
| Score and save | Yes | Yes | No | No |
| Read fraud scores | Yes | Yes | Yes | No |
| Create fraud case | Yes | Yes | No | No |
| Read fraud cases | Yes | Yes | Yes | No |
| Update fraud case | Yes | Yes | No | No |

## Authorization Process

```text
Bearer token received
    |
JWT validated
    |
User loaded from PostgreSQL
    |
Current database role read
    |
Endpoint permission checked
    |
Allowed -> endpoint runs
Denied -> 403 Forbidden
```

## Security Decisions

- Public registration always assigns the viewer role.
- Clients cannot submit their own privileged roles.
- The database role is authoritative.
- JWT role claims are not trusted as the sole authorization source.
- Inactive users are denied access.
- Insufficient permissions return 403 Forbidden.

## Authentication vs Authorization Errors

| Situation | Status |
| --- | --- |
| Missing token | 401 Unauthorized |
| Invalid token | 401 Unauthorized |
| Inactive account | 403 Forbidden |
| Valid user with insufficient role | 403 Forbidden |

## Separation of Duties

Auditors can inspect fraud scores and case records but cannot create or modify operational data.

Fraud analysts can perform scoring and case investigation work but do not automatically receive administrative privileges.

## Conclusion

Role-based authorization limits each user to the operations required by their responsibility. This improves security, supports auditability, and follows the principle of least privilege.
