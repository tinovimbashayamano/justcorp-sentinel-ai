# Feature Selection Report

## Objective
This report summarises the initial feature selection analysis for the IEEE-CIS fraud detection dataset used in the JustCorp Sentinel AI project.

## Purpose of Feature Selection
Feature selection is used to identify which features are likely to be useful, which features need preprocessing, and which features may need to be removed because of high missingness, near-constant values, or leakage risk.

## Checks Performed
The following checks were performed:

- Feature group classification
- Missing-value analysis by feature group
- Near-constant column detection
- Numeric correlation with the fraud target
- High-missingness column identification
- Feature group summary analysis

## Key Findings
Write your findings after running the script.

At minimum, comment on:

- Which feature groups contain the largest number of columns.
- Which feature groups have the highest missingness.
- Whether near-constant columns were detected.
- Which numeric features show the strongest initial relationship with `isFraud`.
- Why correlation is not the final decision method.
- Which features should never be used as input features.

## Initial Feature Selection Decisions
The following initial decisions will guide preprocessing:

1. `TransactionID` will be retained only as an identifier and will not be used as a predictive feature.
2. `isFraud` will be used only as the target variable and must not be used as an input feature.
3. `TransactionAmt` and `TransactionAmt_log` will be considered because amount information is important and skewed.
4. Derived time features such as `transaction_hour` and `transaction_day` will be considered.
5. Low-cardinality categorical features may be encoded.
6. High-cardinality categorical features will require careful treatment.
7. Features with very high missingness will be reviewed before deciding whether to drop, impute, or convert into missingness indicators.
8. Anonymous `C`, `D`, `M`, and `V` features will not be automatically removed because they may contain predictive information.

## Generated Outputs
The following outputs were generated:

- `reports/figures/top_numeric_correlations_with_fraud.png`
- `reports/figures/missingness_by_column_group.png`
- `reports/figures/selected_feature_group_summary.png`
- `reports/model_reports/feature_selection_summary.csv`
- `reports/model_reports/feature_missingness_summary.csv`
- `reports/model_reports/numeric_correlations_with_fraud.csv`


## Recommendations

- Retain anonymous `V` features for now because several of them show the strongest initial relationship with the fraud target.
- Review columns with more than 90% missing values before preprocessing. These columns may be dropped, imputed, or converted into missingness indicators depending on modelling value.
- Review near-constant columns because they may add little useful signal and may increase model complexity.
- Keep `TransactionID` only as an identifier and exclude it from model training.
- Use `isFraud` only as the target variable and never as an input feature.
- Do not rely only on correlation for feature selection because correlation captures linear relationships only. XGBoost and LightGBM can learn non-linear patterns and interactions.
- Use model-based feature importance and validation performance later to refine feature selection.
- Avoid PCA as the first approach because the project requires explainable fraud decisions. Dimensionality reduction may reduce interpretability.
