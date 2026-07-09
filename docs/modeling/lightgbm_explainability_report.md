# LightGBM SHAP Explainability Report

## Objective

This report summarises SHAP explainability analysis for the selected LightGBM fraud detection model.

## Purpose of Explainability

The purpose of explainability is to show why the model assigns fraud risk to transactions. This is important for fraud analysts, auditors, and risk teams because fraud decisions must be understandable and reviewable.

## Model Explained

The explained model is:

- `ml/model_artifacts/lightgbm_fraud_model.joblib`

The model was selected because it achieved the strongest performance during model comparison.

## Explainability Method

SHAP was used to explain model predictions.

SHAP assigns each feature a contribution value showing how much that feature increased or decreased the model prediction for a transaction.

## Global Explainability

The global SHAP analysis identifies the features that most strongly influence the LightGBM fraud model overall.

The top global contributors from the completed SHAP run were:

| Rank | Feature | Mean absolute SHAP value |
|---:|---|---:|
| 1 | numeric__C5 | 0.3337 |
| 2 | numeric__TransactionAmt | 0.2181 |
| 3 | numeric__C13 | 0.1919 |
| 4 | numeric__C14 | 0.1777 |
| 5 | numeric__D3 | 0.1686 |

## Local Explainability

Local explanations were generated for high-risk transactions. These explanations show which features increased or decreased the fraud risk for individual transactions.

## Interpretation

The strongest global drivers were transaction-behaviour counters such as C5, C13, C14, and D3, along with transaction amount. This suggests that the model is relying heavily on behavioural pattern features rather than on the anonymised V features in this sample. The amount feature also appears important, while product, email, identity, and time-based features contributed to the explanation but were not the top-ranked drivers in the generated output.

The local explanations for high-risk cases highlight the specific features that push an individual transaction toward fraud risk. That is useful for fraud investigation because analysts can review the most influential features for a given alert, compare them with known fraud patterns, and justify a case decision. SHAP is especially valuable for audit-ready fraud reporting because it provides a consistent, feature-level explanation for model predictions rather than relying on opaque model output alone.

## Generated Outputs

The SHAP script generated:

- `reports/figures/lightgbm_shap_summary_bar.png`
- `reports/figures/lightgbm_shap_beeswarm.png`
- `reports/model_reports/lightgbm_shap_feature_importance.csv`
- `reports/model_reports/lightgbm_local_explanations.csv`

## Limitations

Some influential features are anonymised, especially `V` features. This means they can help model performance but may be harder to explain in business language. For audit reporting, these features should be described as anonymised transaction-behaviour indicators unless a data dictionary is available.

## Conclusion

SHAP strengthens the model's suitability for an explainable fraud intelligence platform by converting LightGBM predictions into reviewable feature-level evidence. The generated global and local explanations help analysts understand the main fraud-risk drivers, support investigation of high-risk transactions, and provide clearer documentation for audit and governance review.
