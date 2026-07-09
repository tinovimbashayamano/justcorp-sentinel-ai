# Fraud Scoring Storage

## Objective

This document explains how fraud scoring results are stored in the JustCorp Sentinel AI backend.

## Purpose

The purpose of storing fraud scores is to support auditability, fraud investigation, reporting, and future analyst review workflows.

## Database Used

The backend uses PostgreSQL for structured storage.

For local development, the database connection is configured using:

- `DATABASE_URL`

## Table Created

The fraud scoring records are stored in:

- `fraud_score_records`

## Stored Fields

| Field | Purpose |
|---|---|
| `id` | Internal database record ID |
| `transaction_id` | Optional external transaction identifier |
| `model_name` | Name of the model used for scoring |
| `fraud_probability` | Predicted fraud probability |
| `fraud_prediction` | Binary fraud decision |
| `fraud_threshold` | Threshold used for classification |
| `risk_band` | Risk category assigned to the transaction |
| `feature_quality` | Summary of missing and extra submitted features |
| `created_at` | Timestamp when the score was saved |

## API Endpoints

### Score and Save Transaction

```http
POST /api//save
```

This endpoint scores a submitted transaction and saves the scoring result to `fraud_score_records`.

### List Recent Fraud Scores

```http
GET /api/scores
```

This endpoint returns recent saved fraud scoring records. The optional `limit` query parameter controls how many records are returned and accepts values from `1` to `100`.

## Initialization

Create the database table with:

```powershell
.\.venv\Scripts\python.exe -m backend.app.db.init_db
```

## Audit Value

Persisting fraud scores creates a reviewable history of model decisions. This supports investigation workflows, later reporting, and audit checks that need to connect a transaction score to the model name, probability, threshold, risk band, and feature-quality context used at scoring time.

