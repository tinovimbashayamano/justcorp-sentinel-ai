# LightGBM Fraud Detection Model Report

## Objective

This report summarises the LightGBM fraud detection model trained for the JustCorp Sentinel AI project.

## Model Used

The model uses LightGBM, a gradient boosting algorithm based on decision trees.

LightGBM was selected because it is efficient for large tabular datasets and can learn non-linear relationships between transaction features.

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

The LightGBM model achieved the following metrics on the held-out test set.

| Metric | Value |
|---|---:|
| Accuracy | 0.889821 |
| Precision | 0.217665 |
| Recall | 0.828212 |
| F1-score | 0.344730 |
| ROC-AUC | 0.936729 |
| Average precision / PR-AUC | 0.633026 |

## Interpretation

LightGBM improved over the baseline model across all key metrics, including accuracy, recall, ROC-AUC, and PR-AUC. It also outperformed XGBoost on the same test split, with higher precision, recall, F1-score, ROC-AUC, and average precision. The recall is stronger than the precision, which is expected in fraud detection because the model is prioritizing the identification of suspicious transactions even when that increases false positives. The PR-AUC also improved materially, showing better ranking performance for the minority fraud class. LightGBM is well suited to large tabular fraud datasets because it is computationally efficient, handles non-linear patterns well, and scales effectively with many features and rows. This model should still be compared formally against the baseline and XGBoost before a final production selection is made.

## Generated Outputs

The LightGBM training script generated:

- reports/figures/lightgbm_confusion_matrix.png
- reports/figures/lightgbm_precision_recall_curve.png
- reports/figures/lightgbm_feature_importance.png
- reports/model_reports/lightgbm_model_metrics.csv
- reports/model_reports/lightgbm_classification_report.txt
- ml/model_artifacts/lightgbm_fraud_model.joblib

## Conclusion

This LightGBM model provides a stronger benchmark than the baseline and XGBoost models for fraud detection and will be compared directly with both during the final model selection process.
