# Fraud API Testing

## Objective

This document describes the automated tests created for the JustCorp Sentinel AI fraud scoring API.

## Purpose

The purpose of the tests is to confirm that the FastAPI backend starts correctly, the fraud model health endpoint works, and the fraud scoring endpoint returns valid prediction outputs.

## Test File

The tests are stored in:

- `tests/backend/test_fraud_api.py`

## Tests Included

The test suite checks:

- Root backend endpoint
- Fraud model health endpoint
- Fraud scoring endpoint
- Rejection of unsupported `GET` requests on the scoring endpoint

## Model Artifact Handling

The fraud scoring tests require the local LightGBM model artifact:

- `ml/model_artifacts/lightgbm_fraud_model.joblib`

If this artifact is not available, the model-dependent tests are skipped. This prevents the test suite from failing in environments where generated model artifacts are not committed to GitHub.

## Test Command

Run the tests using:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/backend/test_fraud_api.py -q
```
