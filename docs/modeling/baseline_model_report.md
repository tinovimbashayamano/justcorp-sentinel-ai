# Baseline Fraud Detection Model Report

## Objective

This report summarises the first baseline fraud detection model trained for the JustCorp Sentinel AI project.

## Model Used

The baseline model uses SGD Logistic Regression with class weighting.

This model was selected because it is fast, scalable for large datasets, supports probability estimates, and provides a simple benchmark before training more advanced models such as XGBoost and LightGBM.

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

A stratified split was used so that the fraud and non-fraud class proportions were preserved in both sets.

## Evaluation Metrics

Because the dataset is highly imbalanced, accuracy alone is not sufficient.

The following metrics were used:

- Accuracy
- Precision
- Recall
- F1-score
- ROC-AUC
- Average precision / PR-AUC

## Results

The baseline model achieved the following metrics on the held-out test set.

| Metric | Value |
|---|---:|
| Accuracy | 0.7786 |
| Precision | 0.1092 |
| Recall | 0.7445 |
| F1-score | 0.1905 |
| ROC-AUC | 0.8455 |
| Average precision / PR-AUC | 0.3925 |

## Interpretation

The baseline model does detect a meaningful share of fraud cases, as shown by the relatively high recall of 0.7445. However, the low precision of 0.1092 means that many flagged transactions are false positives. Accuracy is not a reliable standalone metric here because the dataset is heavily imbalanced, so a model can appear strong by predicting mostly non-fraud cases while missing many fraudulent ones. PR-AUC is especially important for fraud detection because it measures performance on the minority class and is more informative than accuracy in imbalanced settings. This model is therefore only a benchmark: it provides a useful starting point, but it should be improved with stronger feature engineering and more advanced models such as XGBoost or LightGBM.

## Generated Outputs

The baseline training script generated:

- reports/figures/baseline_confusion_matrix.png
- reports/figures/baseline_precision_recall_curve.png
- reports/model_reports/baseline_model_metrics.csv
- reports/model_reports/baseline_classification_report.txt
- ml/model_artifacts/baseline_sgd_logistic_model.joblib

## Conclusion

This baseline model establishes a reference point for future fraud detection experiments. Its performance will be compared against more advanced models such as XGBoost and LightGBM to determine whether additional complexity produces better recall, precision, and PR-AUC for this imbalanced classification task.
