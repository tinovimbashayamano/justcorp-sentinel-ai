# LightGBM Threshold Tuning Report

## Objective

This report summarises threshold tuning for the LightGBM fraud detection model.

## Purpose of Threshold Tuning

The LightGBM model outputs a fraud probability. A classification threshold is then used to convert that probability into a final fraud or non-fraud decision.

The default threshold is 0.50, but fraud detection often requires threshold tuning because the cost of missing fraud and the cost of false alarms are not equal.

## Model Used

The threshold tuning was performed on:

- `ml/model_artifacts/lightgbm_fraud_model.joblib`

## Dataset

The model was evaluated using the same held-out test split used during model training.

## Evaluation Metrics

The following threshold-level metrics were evaluated:

- Accuracy
- Precision
- Recall
- F1-score
- Predicted fraud count

## Results

The best threshold results after running the script are shown below.

## Default Threshold Comparison

| Threshold | Accuracy | Precision | Recall | F1-score | Predicted fraud count |
|---:|---:|---:|---:|---:|---:|
| 0.50 | 0.889821 | 0.217665 | 0.828212 | 0.344730 | 15,726 |
| 0.84 | 0.974947 | 0.678095 | 0.540769 | 0.601696 | 3,296 |
## Interpretation

The threshold that produced the best F1-score was 0.84. This is higher than the default 0.50 threshold, which means the tuned model is more conservative and favours precision over recall. Threshold tuning matters in fraud detection because the business objective is usually to balance the number of alerts with the quality of those alerts. This threshold is a strong starting point, but it may still need to be adjusted based on fraud operations policy, alert workload, and business tolerance for missed fraud cases.

## Generated Outputs

The threshold tuning script generated:

- `reports/figures/lightgbm_threshold_metrics.png`
- `reports/figures/lightgbm_best_threshold_confusion_matrix.png`
- `reports/model_reports/lightgbm_threshold_tuning.csv`


## Conclusion

The tuned threshold of 0.84 provides a more conservative fraud alerting strategy than the default 0.50 threshold. It substantially improves precision and F1-score while reducing the number of predicted fraud alerts, but it also lowers recall. This threshold is useful when the business wants higher-quality fraud alerts and fewer false positives. However, the final threshold should still be reviewed against operational capacity, investigation workload, and the business cost of missed fraud cases.