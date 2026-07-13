# Fraud Case Review Workflow

## Objective

This document explains the fraud case review workflow added to the JustCorp Sentinel AI backend.

## Purpose

Fraud scores alone are not enough for a fraud intelligence system. Analysts need a workflow for reviewing scored transactions, recording investigation notes, updating case status, and storing final decisions.

## Database Table

Fraud case reviews are stored in:

- `fraud_case_reviews`

## Relationship to Fraud Scores

Each fraud case review is linked to a saved fraud score record using:

- `fraud_score_record_id`

This allows the system to connect analyst decisions back to the original model score, threshold, probability, risk band, and feature-quality summary.

## Stored Fields

| Field | Purpose |
|---|---|
| `id` | Internal case review ID |
| `fraud_score_record_id` | Linked fraud score record |
| `case_status` | Current investigation status |
| `analyst_decision` | Analyst decision on the case |
| `analyst_notes` | Investigation notes |
| `reviewed_by` | Analyst or reviewer name |
| `created_at` | Case creation timestamp |
| `updated_at` | Last update timestamp |

## Supported Case Statuses

| Status | Meaning |
|---|---|
| `open` | Case has been opened but not yet reviewed |
| `under_review` | Analyst is actively reviewing the case |
| `confirmed_fraud` | Analyst confirmed the transaction as fraud |
| `false_positive` | Analyst found that the alert was not fraud |
| `closed` | Case has been closed |

## Supported Analyst Decisions

| Decision | Meaning |
|---|---|
| `pending` | No final decision yet |
| `confirmed_fraud` | Fraud was confirmed |
| `false_positive` | Alert was not fraud |
| `needs_more_information` | More evidence is needed |

## API Endpoints

### Create Case Review

```http
POST /api/v1/fraud/cases
```

### List Case Reviews

```http
GET /api/v1/fraud/cases?limit=5
```

### Get Single Case Review

```http
GET /api/v1/fraud/cases/{case_id}
```

### Update Case Review

```http
PATCH /api/v1/fraud/cases/{case_id}
```

## Audit Value

The review workflow improves auditability because it connects model output to human investigation. It records who reviewed the case, what decision was made, and what notes supported that decision.

## Conclusion

The fraud case review workflow moves the backend from simple fraud scoring toward a practical fraud investigation system. It supports analyst review, audit evidence, and future dashboard case management.
