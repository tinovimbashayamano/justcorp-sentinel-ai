# Fraud Case Evidence

## Objective

Fraud case evidence provides a controlled way to attach investigation files to a fraud case while preserving integrity metadata, access history, actor identity, and the case timeline. The feature supports evidence upload, discovery, download, integrity verification, and soft deletion without storing binary file contents in PostgreSQL, audit logs, or case history.

## Evidence Lifecycle

Evidence moves through the following lifecycle:

```text
Select file and metadata
    |
Validate role, case, filename, extension, MIME type, and size
    |
Generate a unique stored filename
    |
Write the file to evidence storage and calculate SHA-256
    |
Create evidence metadata, custody log, audit log, and case-history event
    |
List, inspect, or download the active evidence
    |
Verify SHA-256 before every download
    |
Soft-delete the evidence when authorized
    |
Retain the file and metadata, but deny subsequent API access
```

An active evidence record has `is_deleted=false`. A soft-deleted record has `is_deleted=true`, identifies the deleting user, and records the deletion timestamp. The API excludes deleted evidence from ordinary lists and treats direct metadata and download requests for it as not found.

## Supported Evidence Categories

Evidence metadata uses one of these categories:

- `transaction`
- `screenshot`
- `bank_statement`
- `customer_document`
- `email`
- `device_log`
- `export`
- `other`

The default category is `other`. An optional description may contain no more than 1,000 characters and is trimmed before storage.

## Upload Flow

Admins and fraud analysts may upload evidence by sending a multipart request containing the file, category, and optional description.

The service performs these steps:

1. Verify that the actor is an admin or fraud analyst.
2. Verify that the fraud case exists.
3. Remove directory components and unsafe characters from the submitted filename.
4. Validate the file extension and declared MIME type.
5. Generate a UUID-based stored filename while preserving the allowed extension.
6. Stream the file to storage in chunks while enforcing the size limit and calculating SHA-256.
7. Insert the `case_evidence` metadata record.
8. Insert an `upload` record into `evidence_access_logs`.
9. Create the `case.evidence.upload` audit record.
10. Create the `case.evidence.uploaded` case-history event.
11. Commit the database work as one transaction.

If file validation or writing fails, partial files are removed. If a database, audit, or history write fails after the file has been written, the database transaction is rolled back and the newly written file is removed. This prevents orphaned files and partial chain-of-custody records.

The current upload endpoint returns `200 OK` after a successful upload. A future API-version change may adopt `201 Created`; clients should follow the documented status for the deployed version.

## File Validation

The upload service accepts these extensions:

| Extension | Accepted MIME types |
|---|---|
| `pdf` | `application/pdf` |
| `png` | `image/png` |
| `jpg`, `jpeg` | `image/jpeg` |
| `csv` | `text/csv`, `application/csv`, `text/plain` |
| `txt` | `text/plain` |
| `json` | `application/json`, `text/json`, `text/plain` |

The maximum upload size is 20 MB. Empty files, unsupported extensions, MIME/extension mismatches, and oversized files are rejected with `400 Bad Request`. Invalid form metadata, such as a description longer than 1,000 characters, is rejected with `422 Unprocessable Entity` by request validation.

Filename sanitization strips path components, normalizes the name, replaces unsafe characters, removes dangerous leading or trailing separators, and limits the result to 255 characters. This prevents a submitted filename from selecting an arbitrary storage path.

MIME validation currently checks the multipart content type supplied with the upload. It does not replace malware scanning, content disarm and reconstruction, or deep file-signature inspection. Those controls should be added before accepting evidence from untrusted production sources.

## Storage Design

Binary evidence is stored outside the application package:

```text
justcorp-sentinel-ai/
    backend/
    docs/
    tests/
    storage/
        evidence/
```

Evidence must never be stored in `backend/app/`. The application resolves storage through `backend/app/core/storage.py`:

```python
BASE_STORAGE_DIR = Path("storage")
EVIDENCE_STORAGE_DIR = BASE_STORAGE_DIR / "evidence"
```

The directory is created automatically when required. Each uploaded file receives a UUID-based stored filename, for example:

```text
cb8af35f7a88450ea0a31f17651cfdaf.pdf
```

The original filename remains in database metadata for investigator display. Two uploads with the same original filename therefore remain independent and receive different stored filenames.

The `case_evidence` table stores:

- evidence and case identifiers
- uploader user ID and preserved username
- original and stored filenames
- storage path
- MIME type and evidence category
- file size in bytes
- SHA-256 digest
- optional description
- deletion state, deleting identity, and deletion timestamp
- creation timestamp

Deleting a fraud case cascades to its evidence metadata. Deleting an uploader or deleting user sets the corresponding user ID to `NULL` while preserving the snapshot username.

## SHA-256 Integrity Verification

SHA-256 is calculated while the upload stream is written. The resulting 64-character hexadecimal digest is stored in `case_evidence.sha256_hash` and returned in evidence metadata.

Before a download is released, the service recalculates SHA-256 from the stored file and compares it with the recorded digest using a timing-safe comparison. The download succeeds only when the values match. A missing file or digest mismatch returns `409 Conflict` and no successful download custody event is recorded.

An investigator can independently verify a downloaded file in PowerShell:

```powershell
$originalHash = (
    Get-FileHash -Path ".\sample-evidence.pdf" -Algorithm SHA256
).Hash.ToLower()

$downloadHash = (
    Get-FileHash -Path ".\downloaded-evidence.pdf" -Algorithm SHA256
).Hash.ToLower()

$originalHash -eq $downloadHash
```

SHA-256 detects accidental or unauthorized file changes. It does not prove who originally created the document, and it is not a digital signature.

## Security Model

Evidence security uses authenticated users, role-based authorization, case-scoped lookups, file validation, integrity verification, and comprehensive interaction logging.

Important controls include:

- every endpoint requires an active authenticated user
- evidence IDs are always checked against the case ID in the URL
- viewers cannot list, inspect, upload, download, or delete evidence
- analysts may delete only evidence they uploaded
- submitted paths cannot control the final storage location
- stored filenames are unpredictable UUID values
- deleted evidence is unavailable through normal metadata and download endpoints
- binary data and document contents are excluded from audit and history records
- access-denied evidence actions create a denied audit record
- successful uploads, downloads, and deletions create custody records

Local filesystem permissions must restrict the evidence directory to the application service account and authorized operations personnel. Production deployments should also provide encryption at rest, encrypted transport, backups, retention controls, malware scanning, and security monitoring.

## Role-Based Access Control

| Role | Upload | List and inspect | Download | Delete |
|---|---:|---:|---:|---:|
| Admin | Allowed | Allowed | Allowed | Any evidence |
| Fraud analyst | Allowed | Allowed | Allowed | Own uploads only |
| Auditor | Denied | Allowed | Allowed | Denied |
| Viewer | Denied | Denied | Denied | Denied |

An unauthorized evidence action returns `403 Forbidden`. A missing case, missing evidence record, evidence/case mismatch, or soft-deleted evidence lookup returns `404 Not Found` where applicable.

## API Endpoints

| Method | Endpoint | Purpose | Successful status |
|---|---|---|---:|
| `POST` | `/api/v1/cases/{case_id}/evidence` | Upload evidence and metadata | `200 OK` |
| `GET` | `/api/v1/cases/{case_id}/evidence` | List active evidence for a case | `200 OK` |
| `GET` | `/api/v1/cases/{case_id}/evidence/{evidence_id}` | Read active evidence metadata | `200 OK` |
| `GET` | `/api/v1/cases/{case_id}/evidence/{evidence_id}/download` | Verify and download evidence | `200 OK` |
| `DELETE` | `/api/v1/cases/{case_id}/evidence/{evidence_id}` | Soft-delete evidence | `200 OK` |

The list endpoint supports `limit` from 1 to 100, defaults to 50, and supports an `offset` of zero or greater. Results are returned oldest first using creation time and evidence ID as the deterministic ordering.

### Upload Request

The upload request uses `multipart/form-data`:

```text
file=<binary file>
category=bank_statement
description=Customer-provided statement
```

### Evidence Metadata

Evidence responses include:

```json
{
  "id": 1,
  "case_id": 3,
  "uploader_user_id": 1,
  "uploader_username": "analyst",
  "original_filename": "sample-evidence.pdf",
  "stored_filename": "cb8af35f7a88450ea0a31f17651cfdaf.pdf",
  "mime_type": "application/pdf",
  "category": "bank_statement",
  "file_size_bytes": 555020,
  "sha256_hash": "8b36c8021bc46867ef62885fae9985620fae89106a0779caca554c1d766fae57",
  "description": "Customer-provided statement",
  "is_deleted": false,
  "deleted_by_user_id": null,
  "deleted_by_username": null,
  "deleted_at": null,
  "created_at": "2026-07-21T09:51:45.994677Z"
}
```

The internal `storage_path` is not returned by the API.

## Soft Deletion

Evidence deletion is logical rather than physical. A successful deletion sets:

- `is_deleted=true`
- `deleted_by_user_id`
- `deleted_by_username`
- `deleted_at`

The original metadata and file remain available to controlled storage and database administration processes for retention, legal hold, and forensic review. The file is not erased from disk by the API.

After deletion:

- list endpoints exclude the record
- direct metadata access returns `404 Not Found`
- download returns `404 Not Found`
- the deletion remains visible in access logs, audit logs, and case history

There is currently no evidence restoration endpoint. Physical deletion, retention expiry, and legal-hold workflows require a separate controlled process.

## Chain of Custody

Every successful upload, download, and deletion creates an `evidence_access_logs` row containing:

- evidence ID
- user ID, when the user still exists
- preserved username
- action: `upload`, `download`, or `delete`
- client IP address
- user agent
- timestamp

Deleting a user sets `user_id` to `NULL` while retaining the username. Access records are ordered using their timestamps and IDs. The table does not store file contents.

Evidence interactions also produce two complementary records.

### Audit Records

| Operation | Audit action |
|---|---|
| Upload | `case.evidence.upload` |
| Download | `case.evidence.download` |
| Delete | `case.evidence.delete` |
| Denied operation | `case.evidence.access_denied` |

Audit records use `resource_type="case_evidence"` and identify the evidence resource when available. Successful action details contain only the evidence ID, original filename, and category. Denied records contain only the case ID and attempted operation. No binary data or document body is copied into the audit log.

Admins and auditors may query evidence audit records through:

```http
GET /api/v1/audit-logs?resource_type=case_evidence
```

### Case-History Records

| Operation | Case-history event |
|---|---|
| Upload | `case.evidence.uploaded` |
| Download | `case.evidence.downloaded` |
| Delete | `case.evidence.deleted` |

Each event contains only:

- evidence ID
- original filename
- category

The file, description, storage path, hash, and document contents are not copied into case history. Authorized users may read the case timeline through:

```http
GET /api/v1/cases/{case_id}/timeline
```

The access log answers who interacted with one evidence item and from which client. The audit log provides system-wide compliance search. Case history explains how evidence activity fits into one investigation. Together, these records form the application-level chain of custody.

## Transaction and Failure Behavior

The evidence metadata, access record, audit entry, and history event for an operation are committed together. A failure rolls back the entire database transaction.

Upload additionally coordinates database state with the filesystem. The service removes the new file if the database transaction fails. Download records are committed only after the file exists and passes SHA-256 verification. Soft deletion does not remove the file and therefore preserves it for controlled retention.

## Future Cloud Storage Support

The local storage path is centralized in `backend/app/core/storage.py`, and the evidence service is the application boundary that reads and writes evidence files. Production deployments can replace local storage with:

- Azure Blob Storage
- Amazon S3
- Google Cloud Storage
- encrypted private object storage

A cloud implementation should preserve the existing evidence metadata, API contracts, authorization rules, SHA-256 checks, audit actions, case-history events, and access logs. Storage-specific operations should be exposed through an adapter that supports write, read, existence check, hash verification, and controlled retention without requiring API handlers to know the provider.

Cloud deployment should also provide:

- server-side encryption with managed or customer-managed keys
- private buckets or containers with public access disabled
- short-lived service credentials and least-privilege identities
- versioning, retention policies, and legal holds
- malware scanning and quarantine before evidence becomes downloadable
- lifecycle rules for archival and approved destruction
- regional residency and backup policies
- provider access logs correlated with application custody records
- multipart upload cleanup and retry handling

Presigned URLs should be used only when their authorization, expiry, checksum, and custody implications are fully controlled. Direct public evidence URLs are not permitted.

## Current Limitations

- Evidence is stored on the local filesystem and is not shared automatically across multiple backend instances.
- The storage directory does not yet provide application-managed encryption at rest.
- MIME validation uses the declared upload content type rather than deep content inspection.
- Antivirus scanning, quarantine, and document sanitization are not implemented.
- There is no restore, legal-hold, retention-expiry, or physical-destruction API.
- The API does not support partial-content or ranged downloads.
- SHA-256 provides integrity detection but not a signer identity or digital signature.
- The evidence access log is currently queried directly from PostgreSQL; there is no dedicated evidence-access-log API endpoint.

## Conclusion

Fraud case evidence combines case-scoped file storage with strict role permissions, safe filenames, UUID storage names, upload limits, SHA-256 verification, soft deletion, and three complementary custody records. The design keeps binary content outside PostgreSQL and secondary logs while preserving the metadata required to investigate access, demonstrate integrity, and migrate to managed cloud object storage in the future.
