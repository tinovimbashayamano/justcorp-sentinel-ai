# Fraud Scoring API

## Objective

This document describes the fraud scoring API endpoint for the JustCorp Sentinel AI backend.

## Purpose

The fraud scoring API allows a transaction to be submitted to the backend and scored using the trained LightGBM fraud detection model.

## Model Used

The API uses the saved LightGBM model artifact:

- `ml/model_artifacts/lightgbm_fraud_model.joblib`

## Threshold Used

The API applies the tuned fraud threshold:

- `0.84`

This threshold was selected during threshold tuning because it produced the best F1-score.

## Endpoints

### Model Health Check

```http
GET /api
```

This endpoint checks whether the fraud scoring model can be loaded and is ready for prediction.

Example response:

```json
{
  "status": "ready",
  "model_name": "lightgbm_fraud_model",
  "model_path": "ml/model_artifacts/lightgbm_fraud_model.joblib",
  "fraud_threshold": 0.84,
  "expected_feature_count": 81
}
```

### Score Transaction

```http
POST /api
```

This endpoint accepts transaction features and returns a fraud score, binary fraud prediction, applied threshold, risk band, and feature-quality summary.

Example request:

```json
{
  "transaction_id": "txn-001",
  "features": {
    "TransactionAmt": 100.0,
    "ProductCD": "W",
    "card1": 12345
  }
}
```

Example response:

```json
{
  "transaction_id": "txn-001",
  "model_name": "lightgbm_fraud_model",
  "fraud_probability": 0.62,
  "fraud_prediction": 0,
  "fraud_threshold": 0.84,
  "risk_band": "medium",
  "feature_quality": {
    "expected_feature_count": 81,
    "missing_features_count": 78,
    "extra_features_count": 0,
    "missing_features_preview": ["card2", "card3"],
    "extra_features_preview": []
  }
}
```

## Request Body

| Field | Type | Required | Description |
|---|---|---:|---|
| `transaction_id` | string or null | No | Optional external transaction identifier. |
| `features` | object | Yes | Transaction feature values used by the fraud model. |

## Response Fields

| Field | Type | Description |
|---|---|---|
| `transaction_id` | string or null | Transaction identifier passed in the request. |
| `model_name` | string | Name of the model used for scoring. |
| `fraud_probability` | number | Predicted probability that the transaction is fraudulent. |
| `fraud_prediction` | integer | Binary fraud decision using the tuned threshold. |
| `fraud_threshold` | number | Threshold used to convert probability into prediction. |
| `risk_band` | string | Risk category assigned from the fraud probability. |
| `feature_quality` | object | Summary of missing or extra submitted features. |

## Risk Bands

| Risk band | Probability range |
|---|---:|
| `high` | `>= 0.84` |
| `medium` | `>= 0.50 and < 0.84` |
| `low` | `>= 0.25 and < 0.50` |
| `very_low` | `< 0.25` |

## Error Responses

If the model artifact cannot be loaded, the API returns `503 Service Unavailable`.

If the transaction cannot be scored because of invalid input or prediction failure, the scoring endpoint returns `400 Bad Request`.
