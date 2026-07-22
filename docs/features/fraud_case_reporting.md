# Fraud Case Reporting and Export Engine

## 1. Overview

The Fraud Case Reporting and Export Engine provides structured, audit-ready
reporting for fraud investigation cases within JustCorp Sentinel AI.

The subsystem aggregates fraud case information and exports it in JSON, CSV or
PDF format. Generated report metadata is persisted in PostgreSQL, while
exported files are stored in the configured report storage directory.

## 2. Objectives

The reporting subsystem supports:

- Fraud case summaries
- Investigation timeline reports
- Investigation task summaries
- Evidence inventory reports
- Audit history summaries
- Complete fraud case reports
- JSON, CSV and PDF exports
- SHA-256 file-integrity verification
- Download tracking
- Soft deletion and restoration
- Role-based reporting permissions

## 3. Supported Report Types

| Report type | Purpose |
|---|---|
| `case_summary` | Core fraud case, score and comment information |
| `investigation_timeline` | Chronological investigation activity |
| `task_summary` | Investigation task status and workload |
| `evidence_inventory` | Evidence records and file metadata |
| `audit_summary` | Case history and authorized audit events |
| `complete_case` | Consolidated fraud investigation report |

## 4. Supported Export Formats

| Format | MIME type | Typical use |
|---|---|---|
| JSON | `application/json` | System integration and structured archival |
| CSV | `text/csv; charset=utf-8` | Spreadsheet and operational analysis |
| PDF | `application/pdf` | Human-readable investigation and audit reports |

Not every report type supports CSV. Complex reports such as `complete_case`
are restricted to formats that preserve nested structures.

## 5. Architecture

### Reporting constants

`backend/app/core/reporting.py` defines report types, formats, statuses,
permissions, MIME types, extensions and storage configuration.

### Generated report model

`backend/app/models/generated_report.py` stores lifecycle information, file
metadata, integrity hashes, download counters and soft-deletion information.

### Reporting schemas

`backend/app/schemas/report.py` validates generation requests, filters, API
responses, deletion, restoration and integrity results.

### Report data service

`backend/app/services/report_data_service.py` collects and normalizes cases,
scores, comments, evidence, tasks, history and authorized audit events.

### Export service

`backend/app/services/report_export_service.py` renders JSON, CSV and PDF,
writes files atomically and calculates SHA-256 hashes.

### Reporting service

`backend/app/services/reporting_service.py` coordinates generation, database
persistence, downloads, integrity verification, deletion and restoration.

### Reporting API

`backend/app/api/reports.py` exposes authenticated report operations.

## 6. Report Lifecycle

A generated report progresses through these states:

1. `pending`
2. `processing`
3. `completed` or `failed`
4. `deleted` when soft-deleted

During generation, the system creates a database record, aggregates case data,
renders and atomically stores the file, calculates its size and SHA-256 hash,
then marks the report completed. A sanitized failure state is persisted if
generation fails.

## 7. File Integrity

Every completed report stores its size, SHA-256 hash, MIME type, stored
filename and storage path. Before download, the service verifies that the file
exists and that its current size and hash match the stored metadata. Missing or
modified files cannot be downloaded.

## 8. Access Control

Administrators, fraud analysts and auditors can view and generate reports.
Additional manager roles are recognized by the reporting router for future
role-model compatibility. Detailed audit data is restricted to administrators
and auditors. Deletion and restoration are administrator-only operations, and
only administrators may include deleted reports in results.

Sensitive-data and internal-comment options are validated separately by the
data service. All endpoints require an active authenticated user.

## 9. API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/v1/reports/cases/{case_id}` | Generate a report |
| GET | `/api/v1/reports/cases/{case_id}` | List reports for one case |
| GET | `/api/v1/reports` | List all reports |
| GET | `/api/v1/reports/{report_id}` | Read report metadata |
| GET | `/api/v1/reports/{report_id}/download` | Download and register access |
| GET | `/api/v1/reports/{report_id}/integrity` | Verify file integrity |
| DELETE | `/api/v1/reports/{report_id}` | Soft delete a report |
| POST | `/api/v1/reports/{report_id}/restore` | Restore retained report data |

## 10. Example Generation Request

```json
{
  "report_type": "complete_case",
  "export_format": "pdf",
  "title": "Complete Fraud Case Report",
  "include_sensitive_data": false,
  "include_internal_comments": false,
  "include_audit_logs": false
}
```

## 11. Storage

Generated files are stored under `storage/reports/`. Report contents must not
be committed to source control; only `.gitkeep` is tracked.

## 12. Security Controls

- Authentication on every endpoint
- Role-based authorization
- Sensitive-field filtering
- Restricted audit data
- Safe filename generation
- Storage-path containment checks
- Atomic file writing
- SHA-256 integrity verification
- No-cache download headers
- Soft-deletion metadata
- Download counters and timestamps

## 13. Limitations and Future Improvements

Report generation is currently synchronous. Potential improvements include:

- Background task processing and generation queues
- Object-storage integration
- Encrypted report storage
- Signed temporary download URLs
- Configurable retention rules
- Report branding templates
- Scheduled compliance reports
- Completion email notifications
