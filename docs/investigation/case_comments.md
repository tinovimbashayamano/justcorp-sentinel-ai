# Fraud Case Comments

## Objective

Fraud case comments provide a controlled collaboration channel for investigators working on a case. The feature preserves authorship, visibility, edits, deletion state, case-history events, and audit evidence without exposing sensitive comment content through secondary logs.

## Collaboration Model

Comments belong to one fraud case and have one preserved author identity. Only admins and fraud analysts can create comments. Authors may edit and delete their own comments, while admins may edit and delete any comment. Auditors can only read auditor-visible comments, and viewers have no access.

Comments support investigator collaboration without making every discussion visible to auditors. Visibility is selected when a comment is created and may be changed through an authorized edit.

## Comment Table

Current comment state is stored in `case_comments`. Each record references a fraud case and, when the author still exists, a user. Deleting a fraud case cascades to its comments. Deleting a user sets the comment's user reference to `NULL` while preserving the recorded username.

The table retains comment content after soft deletion for compliance purposes. Standard API serialization prevents that retained content from being returned to ordinary readers.

## Revision Table

Previous comment states are stored in `case_comment_revisions`. A revision references its comment with `ON DELETE CASCADE` and records the editor's user ID and preserved username.

Edits preserve prior versions by recording the previous content and visibility before the current comment is changed. This prevents an edit from replacing investigation evidence without traceability.

## Stored Fields

The comment table stores:

- comment and case identifiers
- author user ID and preserved username
- comment content
- visibility
- edited and deleted flags
- deleting user ID and preserved username
- deletion timestamp
- creation and update timestamps

The revision table stores:

- revision and comment identifiers
- editor user ID and preserved username
- previous content and visibility
- revision creation timestamp

## Visibility Levels

`internal` comments are visible to admins and fraud analysts. They are not visible to auditors or viewers.

`auditor_visible` comments are visible to admins, fraud analysts, and auditors. Viewers cannot access them.

An auditor requesting a specific internal comment receives `404 Not Found` rather than `403 Forbidden`. This prevents disclosure that the internal resource exists.

## Role Permissions

| Role | Create | Read internal | Read auditor-visible | Edit | Delete |
|---|---:|---:|---:|---:|---:|
| Admin | Allowed | Allowed | Allowed | Any comment | Any comment |
| Fraud analyst | Allowed | Allowed | Allowed | Own comments | Own comments |
| Auditor | Denied | Denied | Allowed | Denied | Denied |
| Viewer | Denied | Denied | Denied | Denied | Denied |

## Comment Creation

Admins and fraud analysts may create comments with either visibility level. Content is trimmed, must contain at least one non-whitespace character, and may contain no more than 5,000 characters.

Creating a comment records the author, creates a structured case-history event, creates an audit record, and commits all related records together.

## Comment Editing

Authors may edit their own non-deleted comments. Admins may edit any non-deleted comment. Another fraud analyst cannot edit the author's comment, and auditors and viewers cannot edit comments.

An edit may change content, visibility, or both. An unchanged request is idempotent: it does not create a revision, history event, or audit record. A successful change sets `is_edited` to `true`.

## Revision History

A revision is created before an authorized change is applied. It preserves the previous content, previous visibility, editor identity, and edit timestamp.

Revisions are returned chronologically by creation time and then revision ID. Admins and fraud analysts may read revisions. Auditors may read revisions only when the current comment is auditor-visible. Viewers cannot read revisions.

## Soft Deletion

Deletion is soft deletion. The comment row and its original content remain in the database, while `is_deleted`, deletion identity, and deletion timestamp are recorded.

Deleted content is masked in normal API responses and replaced with:

```text
[comment deleted]
```

Deleted comments remain in their chronological position, cannot be edited, and do not expose their retained content through standard read or list endpoints. Repeating an authorized deletion is idempotent.

## Case-History Integration

Comment actions create structured case-history events:

| Action | Event |
|---|---|
| Create | `case.comment.created` |
| Edit | `case.comment.updated` |
| Delete | `case.comment.deleted` |

History details contain identifiers, usernames, visibility, or changed field names as appropriate. The full comment body is not copied into case history. The legacy `case.comment_added` event remains available only for backward compatibility with analyst-note updates.

## Audit Integration

Comment operations use these audit actions:

- `case.comment.create`
- `case.comment.update`
- `case.comment.delete`
- `case.comment.access_denied`

Audit records use `resource_type="case_comment"` and the comment ID as the resource ID. Audit logs do not store the full comment body. They contain limited metadata such as the case ID, visibility, operation, and changed field names.

## Ordering and Pagination

Comments are returned oldest first using `created_at` ascending and comment ID ascending as a deterministic tie-breaker. Deleted comment markers remain in the same ordering position as the original comment.

The list endpoint supports:

- `limit`, from 1 to 100, defaulting to 50
- `offset`, zero or greater, defaulting to 0

The response includes the visible-item total, limit, offset, and paginated items. Auditor totals include only auditor-visible comments.

## Sensitive Data Rules

Comments should contain only information required for an investigation. Passwords, access tokens, authentication secrets, and unnecessary sensitive transaction data must not be entered in comments.

The full comment body is stored only in the comment and revision tables where required for investigation integrity. It is excluded from case-history details and audit logs. Soft-deleted content is masked in normal API responses.

## Transaction Integrity

Comment creation commits the comment, case-history entry, and audit record atomically. Editing commits the revision, updated comment, history event, and audit record atomically. Deletion commits the soft-delete state, history event, and audit record atomically.

If any related write fails, the transaction is rolled back so no partial comment, revision, history, or audit state remains.

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/v1/cases/{case_id}/comments` | Create a comment |
| `GET` | `/api/v1/cases/{case_id}/comments` | List visible comments |
| `GET` | `/api/v1/cases/{case_id}/comments/{comment_id}` | Read one visible comment |
| `PATCH` | `/api/v1/cases/{case_id}/comments/{comment_id}` | Edit an authorized comment |
| `DELETE` | `/api/v1/cases/{case_id}/comments/{comment_id}` | Soft-delete an authorized comment |
| `GET` | `/api/v1/cases/{case_id}/comments/{comment_id}/revisions` | Read revision history |

A comment must belong to the case identified in the URL. Missing cases, missing comments, and case/comment mismatches return `404 Not Found`.

## Limitations

- Comments do not support attachments, mentions, reactions, or threaded replies.
- There is no dedicated investigation-manager role.
- Soft-deleted content remains available in the database for compliance and revision integrity.
- Visibility applies to the entire comment rather than selected fields or users.
- The API does not currently support restoring deleted comments.
- Comment edits do not use optimistic locking for simultaneous updates.

## Future Enhancements

Potential enhancements include:

- evidence attachments with custody tracking
- threaded discussions and analyst mentions
- notifications for new or updated comments
- comment restoration under a controlled compliance workflow
- team-specific visibility levels
- immutable revision verification
- optimistic concurrency controls
- retention and archival policies
- search across authorized comment content

## Conclusion

Fraud case comments provide role-aware investigation collaboration with retained authorship, versioned edits, soft deletion, response masking, structured case history, privacy-conscious auditing, and atomic transaction handling.
