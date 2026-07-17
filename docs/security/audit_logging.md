# Audit Logging

## Objective

This document describes audit logging for security, compliance, and fraud investigation activities in JustCorp Sentinel AI.

## Purpose

Audit logs provide evidence of who performed important actions, what resources were affected, when the actions occurred, and whether they succeeded.

## Audit Table

Audit records are stored in:

- `audit_logs`

## Recorded Fields

- user ID
- actor username
- action
- status
- resource type
- resource ID
- IP address
- user agent
- safe contextual details
- creation timestamp

## Recorded Events

### Authentication

- successful login
- failed login
- logout
- logout-all
- password change

### Administration

- user role change
- user activation or deactivation
- denied administrative access

### Fraud Operations

- fraud scoring
- persisted fraud result
- case creation
- case update

## Access Control

| Role | Access |
|---|---|
| Admin | Read audit logs |
| Auditor | Read audit logs |
| Fraud analyst | Denied |
| Viewer | Denied |

## Sensitive Data Rules

Audit records must never contain:

- plaintext passwords
- password hashes
- access tokens
- refresh tokens
- authorization headers
- database credentials

## Append-Only Principle

The API provides read access but no ordinary update or delete endpoint for audit logs.

## Filtering

Audit logs can be filtered by:

- action
- status
- actor username
- resource type

Pagination is supported through:

- `limit`
- `offset`

## Reliability Decision

Audit persistence uses safe best-effort logging. A failure to write an audit record is logged internally and does not automatically fail the original business operation.

A stricter regulated deployment may require atomic business and audit transactions.

## Limitation

Application administrators with direct database access can still modify database records. Stronger tamper resistance could later use:

- restricted database roles
- cryptographic hash chaining
- external immutable log storage
- write-once retention systems

## Conclusion

Audit logging establishes a queryable compliance trail across authentication, administration, fraud scoring, and investigation workflows.
