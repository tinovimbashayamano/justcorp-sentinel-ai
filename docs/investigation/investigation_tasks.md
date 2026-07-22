# Investigation Tasks and Analyst Workflow

## Purpose

Investigation tasks represent controlled units of work attached to fraud cases. They support assignment, prioritisation, deadlines, workflow tracking, completion records, cancellation records, audit logging, and case-history visibility.

Tasks are separate from comments and evidence. A comment records investigation discussion, evidence preserves supporting files, and a task records work that must be performed.

## Task Statuses

| Status | Meaning |
|---|---|
| `pending` | Work has not started |
| `in_progress` | Work is actively being performed |
| `blocked` | Work is waiting on a dependency |
| `completed` | Work was successfully completed |
| `cancelled` | Work is no longer required |

## Priorities

- `low`
- `medium`
- `high`
- `critical`

New tasks default to `pending` status and `medium` priority.

## Valid Workflow Transitions

- `pending -> in_progress`
- `pending -> blocked`
- `pending -> cancelled`
- `in_progress -> blocked`
- `in_progress -> completed`
- `in_progress -> cancelled`
- `blocked -> pending`
- `blocked -> in_progress`
- `blocked -> cancelled`

Completed and cancelled tasks are terminal and cannot be edited through the ordinary task endpoints. Reopening a terminal task would require a future dedicated operation with stronger authorization and auditing.

Ordinary status changes cannot set `completed` or `cancelled`. Those states use dedicated endpoints so the system can require and preserve completion or cancellation details.

## Creation and Editable Details

An admin or fraud analyst can create a task. A title is required, is trimmed, and must contain between 3 and 200 characters. Descriptions are optional, are trimmed, convert to `null` when blank, and may contain no more than 5,000 characters.

A due date is optional. When supplied, it must include timezone information, must be in the future at request time, and is normalized to UTC. Editable task details include:

- title
- description
- priority
- due date

Description and due date use explicit clear flags during partial updates so the API can distinguish an omitted field from a deliberate removal.

## Assignment

Tasks may be assigned only to active users with approved investigation roles. In the current application, admins and fraud analysts are valid assignment targets. User existence, active status, and role are verified from the database; request-supplied role information is never trusted.

Assignment, reassignment, and unassignment are independently audited and added to case history. Changing assignment through the dedicated assignment endpoint is restricted to administrators because the current user model does not define a separate risk-manager role.

Assigning a task to its current assignee or unassigning an already unassigned task returns `409 Conflict`.

## Completion

Tasks must be in `in_progress` status before completion. A completion note of between 3 and 5,000 characters is required. The system records:

- completing user ID
- preserved completing username
- completion timestamp
- completion note

Admins may complete a task. A fraud analyst may complete only a task assigned to that analyst.

## Cancellation

Cancellation requires a reason of between 3 and 2,000 characters and records the cancelling user and timestamp. A pending, in-progress, or blocked task may be cancelled. Cancellation is restricted to administrators in the current role model.

## Overdue Tasks

A task is overdue when:

- it has a due date earlier than the current UTC time;
- it has not been completed or cancelled; and
- it has not been deleted.

Task responses contain a calculated `is_overdue` field. It is not persisted as a separate database value. The list endpoint supports `overdue_only=true` and performs the equivalent filtering in the database.

## Soft Deletion

Task deletion is logical rather than physical. Deleted tasks remain available in PostgreSQL for compliance and audit records but are excluded from normal API results. Soft deletion records:

- `is_deleted=true`
- deleting user ID
- preserved deleting username
- deletion timestamp

Only administrators may delete tasks. After deletion, normal list endpoints exclude the task and direct reads return `404 Not Found`.

## Role-Based Access Control

| Operation | Admin | Fraud analyst | Auditor | Viewer |
|---|---:|---:|---:|---:|
| List/read | Allowed | Allowed | Allowed | Denied |
| Create | Allowed | Allowed | Denied | Denied |
| Update details | Allowed | Allowed | Denied | Denied |
| Assign/reassign/unassign | Allowed | Denied | Denied | Denied |
| Change ordinary status | Allowed | Assigned tasks only | Denied | Denied |
| Complete | Allowed | Assigned tasks only | Denied | Denied |
| Cancel | Allowed | Denied | Denied | Denied |
| Soft-delete | Allowed | Denied | Denied | Denied |

All actor identity is derived from the authenticated user. Clients cannot provide creator, completer, canceller, or deleting-user fields.

## Auditability

Task creation, modification, assignment, status changes, completion, cancellation, and deletion create both an audit-log record and a fraud-case history record in the same database transaction as the task change.

Audit actions are:

- `investigation_task.created`
- `investigation_task.updated`
- `investigation_task.assigned`
- `investigation_task.reassigned`
- `investigation_task.unassigned`
- `investigation_task.status_changed`
- `investigation_task.completed`
- `investigation_task.cancelled`
- `investigation_task.deleted`

Case-history events are:

- `case.task.created`
- `case.task.updated`
- `case.task.assigned`
- `case.task.reassigned`
- `case.task.unassigned`
- `case.task.status_changed`
- `case.task.completed`
- `case.task.cancelled`
- `case.task.deleted`

Records include operational metadata such as case ID, task ID, title, status, priority, and assignment. They do not include access tokens, passwords, task descriptions, completion notes, cancellation reasons, identity evidence, or full customer financial records.

If task, audit, or case-history persistence fails, the transaction is rolled back. A task change therefore cannot commit without its compliance records.

## Endpoints

All endpoints require authentication and use the `/api/v1` prefix.

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/v1/fraud-cases/{case_id}/tasks` | Create task |
| `GET` | `/api/v1/fraud-cases/{case_id}/tasks` | List active tasks |
| `GET` | `/api/v1/fraud-cases/{case_id}/tasks/{task_id}` | Read task |
| `PATCH` | `/api/v1/fraud-cases/{case_id}/tasks/{task_id}` | Update editable details |
| `PATCH` | `/api/v1/fraud-cases/{case_id}/tasks/{task_id}/assignment` | Change assignment |
| `PATCH` | `/api/v1/fraud-cases/{case_id}/tasks/{task_id}/status` | Change ordinary status |
| `POST` | `/api/v1/fraud-cases/{case_id}/tasks/{task_id}/complete` | Complete task |
| `POST` | `/api/v1/fraud-cases/{case_id}/tasks/{task_id}/cancel` | Cancel task |
| `DELETE` | `/api/v1/fraud-cases/{case_id}/tasks/{task_id}` | Soft-delete task |

The list endpoint supports:

- `limit`, from 1 to 100, defaulting to 50
- `offset`, zero or greater, defaulting to 0
- `status`, using a controlled task status
- `assigned_to_user_id`, using a positive user ID
- `overdue_only`, defaulting to `false`

Tasks are returned newest first using creation time and task ID as a deterministic tie-breaker.

## Database Integrity

Each task belongs to one fraud case. Deleting the parent case cascades to its tasks. User references use `ON DELETE SET NULL`, while snapshot usernames preserve historical identity after a user record is removed.

PostgreSQL provides server defaults for status, priority, deletion state, creation time, and update time. Indexes support case timelines, status filters, assignee workload, due-date searches, overdue filtering, and exclusion of deleted tasks.

## Limitations and Future Enhancements

- The current application has no manager or risk-manager role; admin performs elevated task operations.
- Terminal tasks cannot currently be reopened.
- The system does not yet send deadline reminders or escalation notifications.
- Task dependencies and subtasks are not modeled.
- Workload dashboards and SLA reporting are not yet exposed through dedicated endpoints.
- Task read events are not currently persisted as audit records.

Future enhancements may add controlled reopening, manager roles, reminders, dependency graphs, recurring tasks, team queues, SLA dashboards, and notification integrations.
