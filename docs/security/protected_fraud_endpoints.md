# Protected Fraud Endpoints

## Objective

This document describes the authentication protection applied to the JustCorp Sentinel AI fraud API.

## Purpose

Fraud scoring, stored fraud records, and investigation cases contain sensitive operational information. These endpoints must not be accessible anonymously.

## Authentication Requirement

All endpoints under:

- `/api/v1/fraud`

require a valid JWT access token.

The client must send:

```http
Authorization: Bearer <access_token>
```

## Protected Operations

The protected router includes:

- Fraud model health
- Transaction scoring
- Scoring and persistence
- Fraud score history
- Case creation
- Case retrieval
- Case updates

## Authentication Process

```text
Request received
    |
Bearer token extracted
    |
JWT signature and expiration validated
    |
sub claim read
    |
User loaded from PostgreSQL
    |
Account status checked
    |
Fraud endpoint executed
```

## Failure Responses

| Situation | Response |
| --- | --- |
| Missing token | 401 Unauthorized |
| Invalid token | 401 Unauthorized |
| Expired token | 401 Unauthorized |
| User does not exist | 401 Unauthorized |
| Inactive user | 403 Forbidden |

## Public Health Endpoint

The general application endpoint remains public:

```http
GET /health
```

The model-specific endpoint is protected:

```http
GET /api/v1/fraud/health
```

## Current Limitation

At this stage, every authenticated active user can access the fraud router.

Role-specific permissions will be introduced in the next stage.

## Conclusion

Authentication protection prevents anonymous access to fraud scoring, stored results, and case investigation information. It establishes the identity boundary required before role-based authorization is applied.
