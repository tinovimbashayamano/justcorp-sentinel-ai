# Case History

## Objective

This document describes the chronological investigation timeline for fraud cases in JustCorp Sentinel AI.

## Timeline Architecture

Every supported case workflow change automatically creates a `case_history` record through the case service. The timeline is stored separately from the current `fraud_case_reviews` state so investigators can understand how a case evolved.

```text
Case create or update
    |
Validate requested changes
    |
Persist current case state
    |
Create history event for each actual workflow change
    |
Read events from oldest to newest
```

No history event is created when a submitted value matches the existing value.

## Stored Fields

Each history record contains:

- history ID
- case ID
- user ID, when the actor still exists
- preserved actor username
- event type
- JSON event details
- creation timestamp

Deleting a case cascades to its timeline. Deleting a user sets the history `user_id` to `NULL` while preserving `actor_username`.

## Event Types

- `case.created`
- `case.status_changed`
- `case.priority_changed`
- `case.assigned`
- `case.comment_added`
- `case.closed`
- `case.reopened`

Comment events record that a note changed without copying confidential note contents into timeline details.

## API Endpoint

```http
GET /api/v1/cases/{case_id}/timeline
```

The endpoint returns the complete timeline for an existing case.

## Access Control

| Role | Access |
|---|---|
| Admin | Allowed |
| Fraud analyst | Allowed |
| Auditor | Allowed |
| Viewer | Denied |

## Ordering

Timeline entries are returned by `created_at` ascending and then by history ID ascending. This produces deterministic, oldest-to-newest investigation history even when multiple events share a timestamp.

## Relationship to Audit Logs

Case history and audit logs serve related but distinct purposes:

- `case_history` is the domain timeline for one fraud investigation.
- `audit_logs` is the broader compliance record across authentication, administration, fraud scoring, and case operations.

A case action may therefore produce both records. Case history explains how the investigation changed, while the audit log supports cross-system security and compliance queries.

## Future Enhancements

Potential extensions include:

- evidence attachments
- dedicated threaded comments
- evidence custody tracking
- external evidence references
- digital signatures
- immutable timeline verification

## Conclusion

Case history preserves a chronological, role-protected investigation narrative while keeping the current case record focused on its latest state.
