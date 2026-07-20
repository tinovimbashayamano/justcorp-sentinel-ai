# Fraud Case Assignment

## Objective

This document describes how JustCorp Sentinel AI assigns fraud cases to analysts, records ownership changes, reports analyst workload, and protects assignment operations.

## Ownership Model

A fraud case may have one user-backed owner through `assigned_to_user_id`. The field is nullable, so newly created cases may remain unassigned until an administrator selects an eligible analyst.

The ownership foreign key references `users.id` with `ON DELETE SET NULL`. Deleting an analyst therefore leaves the case intact and returns it to an unassigned state. Case responses expose both `assigned_to_user_id` and `assigned_to_username`.

Only active users with the `fraud_analyst` role can own a case.

## Assignment Rules

- Assignment is optional and is never required when a case is created.
- Only administrators can assign, reassign, or unassign cases.
- The target user must exist, be active, and have the `fraud_analyst` role.
- Assigning a case to its current analyst is idempotent and does not create duplicate history or audit records.
- Assignment state, case history, and the audit record are committed atomically.

## Assignment Endpoints

### Assign or Reassign

```http
PATCH /api/v1/cases/{case_id}/assignment
Content-Type: application/json
```

```json
{
  "assigned_to_user_id": 4
}
```

The identifier must be a positive integer. The endpoint returns the updated fraud case, including the assignee identifier and username.

### Unassign

```http
DELETE /api/v1/cases/{case_id}/assignment
```

The DELETE endpoint has no request body. It records `manual_unassignment` as the timeline reason.

### Analyst Workload

```http
GET /api/v1/cases/assignments/workload
```

The workload endpoint is available only to administrators.

## Role Permissions

| Role | Assign | Reassign | Unassign | View assignment |
|---|---:|---:|---:|---:|
| Admin | Allowed | Allowed | Allowed | Allowed |
| Fraud analyst | Denied | Denied | Denied | Allowed |
| Auditor | Denied | Denied | Denied | Allowed |
| Viewer | Denied | Denied | Denied | Denied |

Assignment details are visible through the existing case endpoints, which allow administrators, fraud analysts, and auditors but deny viewers.

## Eligible Analyst Requirements

An assignment target is eligible only when all the following conditions are true:

- the user record exists
- the account is active
- the role is `fraud_analyst`

Administrators, auditors, viewers, inactive analysts, and missing users cannot become case owners. A missing case or target user produces a `404` response. An existing but ineligible target is rejected with a `400` response.

## Reassignment Behavior

Assigning a case owned by Analyst A to Analyst B updates the owner and creates a `case.reassigned` timeline event. Event details preserve both analysts' user identifiers and usernames.

The corresponding audit action is `case.assignment.reassigned`. Submitting the current analyst again leaves the case unchanged and creates no additional timeline or audit entry.

## Unassignment Behavior

Unassignment clears `assigned_to_user_id` and creates a `case.unassigned` timeline event. The event preserves the previous analyst identifier and username, sets the new assignee fields to `null`, and records the reason `manual_unassignment`.

The corresponding audit action is `case.assignment.unassigned`. Unassigning an already unassigned case is idempotent and creates no additional timeline or audit entry.

## Workload Calculation

The workload endpoint reports every active fraud analyst, including analysts with no assigned active cases. It returns:

- `open_cases`: assigned cases in the `open` state
- `investigating_cases`: assigned cases in the `investigating` state
- `total_active_cases`: the sum of open and investigating cases

Closed and all other non-active case states are excluded. Results are ordered by `total_active_cases` ascending, with analyst ID used as a deterministic tie-breaker. This places the least-loaded eligible analysts first.

## Timeline Integration

Ownership changes are included in the case timeline:

| Change | Timeline event |
|---|---|
| Unassigned to analyst | `case.assigned` |
| Analyst A to Analyst B | `case.reassigned` |
| Analyst to unassigned | `case.unassigned` |

Assignment and reassignment details contain the old and new assignee identifiers and usernames. Timeline entries identify the administrator who performed the action.

## Audit Integration

Assignment operations create compliance audit records using these actions:

- `case.assignment.assigned`
- `case.assignment.reassigned`
- `case.assignment.unassigned`

Audit records use `resource_type="fraud_case"` and the case ID as `resource_id`. Details contain only the previous and new assignee usernames; credentials, tokens, analyst notes, and sensitive transaction data are not included.

## Filtering

The fraud case listing endpoint supports ownership filters:

```http
GET /api/v1/fraud/cases?assigned_to_user_id=4
GET /api/v1/fraud/cases?unassigned=true
```

`assigned_to_user_id` must be a positive integer. It cannot be combined with `unassigned=true`; conflicting filters return `422 Unprocessable Entity`.

Case listings eager-load the assigned user relationship to avoid one user query per case.

## Limitations

- Assignment management is restricted to administrators; there is no manager role.
- Cases are not assigned automatically based on workload.
- The unassignment endpoint stores a generic reason and does not accept a custom reason body.
- The legacy free-text `assigned_to` field remains available for compatibility but is separate from user-backed ownership.
- Assignment changes do not currently use optimistic locking, so concurrent administrator updates follow normal database last-write behavior.

## Future Enhancements

Potential extensions include:

- a fraud investigation manager role
- automatic or suggested assignment using workload and analyst skills
- custom unassignment and reassignment reasons
- analyst availability, leave, and capacity limits
- team or regional ownership queues
- assignment notifications and escalation rules
- optimistic concurrency checks for simultaneous updates
- service-level targets and aging metrics in workload reporting
