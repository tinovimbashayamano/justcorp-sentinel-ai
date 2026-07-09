# LightGBM Inference Pipeline Report

## Objective

This report explains the inference pipeline used to score transactions with the selected LightGBM fraud detection model.

## Purpose

The purpose of the inference pipeline is to load the trained LightGBM model, score transaction records, assign fraud probabilities, apply the tuned threshold, and return fraud-risk decisions.

## Model Used

The inference script uses:

- `ml/model_artifacts/lightgbm_fraud_model.joblib`

## Dataset Used for Test Inference

The script scores a small sample from:

- `data/processed/baseline_modeling_dataset.csv.gz`

This sample is used only to validate that the saved model can be loaded and used for prediction.

## Threshold Used

The inference pipeline uses the tuned threshold:

- `0.84`

This threshold was selected because it produced the best F1-score during threshold tuning.

## Inference Outputs

For each scored transaction, the script generates:

- `fraud_probability`
- `fraud_prediction`
- `fraud_threshold`
- `risk_band`

## Risk Bands

The following risk bands are used:

| Risk band | Probability range |
|---|---:|
| `high` | `>= 0.84` |
| `medium` | `>= 0.50 and < 0.84` |
| `low` | `>= 0.25 and < 0.50` |
| `very_low` | `< 0.25` |

## Generated Output

The script generates:

- `reports/model_reports/lightgbm_scored_sample_transactions.csv`

This output is not committed to GitHub because it is a generated report file.

## Interpretation

The inference script loaded the saved LightGBM model successfully and generated fraud probabilities for a 20-transaction validation sample. The tuned threshold of `0.84` was applied to convert fraud probabilities into binary fraud predictions.

The scored sample produced the following risk-band distribution:

| Risk band | Transaction count |
|---|---:|
| `high` | 5 |
| `medium` | 6 |
| `low` | 2 |
| `very_low` | 7 |

The prediction distribution was:

| Fraud prediction | Transaction count |
|---:|---:|
| 0 | 15 |
| 1 | 5 |

Risk bands support fraud review by giving analysts a prioritised queue instead of only a binary decision. High-risk transactions can be escalated first, medium-risk transactions can be reviewed with additional context, and low or very-low-risk transactions can be handled with lighter monitoring.

This inference pipeline is needed before API integration because it confirms that the persisted model can be loaded, receives the expected feature schema, returns probabilities, applies the tuned decision threshold, and produces output fields that a backend service can expose consistently.

## Conclusion

This inference pipeline prepares the LightGBM model for backend integration by turning the trained model artifact into a repeatable scoring workflow. It validates the model loading path, prediction logic, thresholding behaviour, risk-band assignment, and generated output schema that the API layer can later reuse.
