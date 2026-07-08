# XGBoost Fraud Detection Model Report

## Objective

This report summarises the XGBoost fraud detection model trained for the JustCorp Sentinel AI project.

## Model Used

The model uses XGBoost, a gradient boosting algorithm based on decision trees.

XGBoost was selected because it can learn non-linear relationships, handle mixed feature patterns, and often performs strongly on tabular fraud detection datasets.

## Dataset

The model was trained using:

- data/processed/baseline_modeling_dataset.csv.gz

The dataset contains:

- 590,540 rows
- 81 input features
- Target variable: isFraud

## Train-Test Split

The dataset was split into:

- 80% training data
- 20% testing data

A stratified split was used to preserve the fraud and non-fraud proportions.

## Class Imbalance Handling

The model used scale_pos_weight to account for class imbalance.

This helps the model give more importance to fraud cases during training.

## Evaluation Metrics

The following metrics were used:

- Accuracy
- Precision
- Recall
- F1-score
- ROC-AUC
- Average precision / PR-AUC

## Results

The XGBoost model achieved the following metrics on the held-out test set.

| Metric | Value |
|---|---:|
| Accuracy | 0.8625 |
| Precision | 0.1747 |
| Recall | 0.7871 |
| F1-score | 0.2860 |
| ROC-AUC | 0.9037 |
| Average precision / PR-AUC | 0.5350 |

## Interpretation

XGBoost improved over the baseline model on nearly every metric, especially ROC-AUC and PR-AUC. The recall increased from 0.7445 to 0.7871, which means the model detected more fraud cases, while the precision remained low at 0.1747. This is a common outcome in highly imbalanced fraud detection tasks where improving recall often increases false positives. PR-AUC also improved substantially, which is important because it better reflects minority-class performance than accuracy. XGBoost is more suitable than the baseline for this task because it can model non-linear interactions and capture more complex fraud patterns. It is still not necessarily the final model, however, and should be compared with LightGBM before a production decision is made.

## Generated Outputs

The XGBoost training script generated:

- reports/figures/xgboost_confusion_matrix.png
- reports/figures/xgboost_precision_recall_curve.png
- reports/figures/xgboost_feature_importance.png
- reports/model_reports/xgboost_model_metrics.csv
- reports/model_reports/xgboost_classification_report.txt
- ml/model_artifacts/xgboost_fraud_model.joblib

## Conclusion

This XGBoost model provides a stronger benchmark than the baseline and will be compared directly against the baseline SGD model and future LightGBM experiments to determine the best-performing fraud detection approach.
