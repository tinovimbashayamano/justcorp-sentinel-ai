# Fraud Storage API Testing

## Objective

This document describes the automated tests for the fraud score storage endpoints.

## Purpose

The purpose of these tests is to confirm that fraud scoring results can be saved to the database and retrieved through the API.

## Test File

The tests are stored in:

- `tests/backend/test_fraud_storage_api.py`

## Endpoints Tested

The test suite checks:

- `POST /api/v1/fraud/score/save`
- `GET /api/v1/fraud/scores?limit=5`
- Limit validation for `GET /api/v1/fraud/scores`

## Test Database Strategy

The tests use an isolated in-memory SQLite database instead of the local PostgreSQL database.

This prevents automated tests from modifying real development data while still validating SQLAlchemy models, database sessions, API routing, and response schemas.

## Model Artifact Handling

The score-and-save tests require the local LightGBM model artifact:

- `ml/model_artifacts/lightgbm_fraud_model.joblib`

If the model artifact is missing, model-dependent tests are skipped.

## Test Command

Run the tests using:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/backend/test_fraud_storage_api.py -q
```
