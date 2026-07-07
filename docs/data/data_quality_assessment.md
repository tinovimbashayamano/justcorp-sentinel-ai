# Data Quality Assessment

## Objective

This report summarises the initial data quality assessment performed on the IEEE-CIS fraud detection dataset.

## Datasets Assessed

| Dataset | Rows | Columns |
|---|---:|---:|
| train_transaction.csv | 590,540 | 394 |
| train_identity.csv | 144,233 | 41 |

## Data Quality Checks Performed

The following checks were performed:

- Missing-value analysis
- Duplicate `TransactionID` checks
- Identity coverage assessment
- Target imbalance review
- Transaction amount anomaly checks
- Near-constant column checks
- High-cardinality categorical feature checks

## Key Findings

Duplicate TransactionID values were not observed in either dataset. Approximately 24.4% of transactions have matching identity records, meaning that most transactions do not have a corresponding identity row. The columns with the highest missing values are mostly identity-related features such as id_24, id_25, and id_07, while transaction features like dist2 and D7 also show substantial missingness. Transaction amounts contain a long tail of extreme values, and the IQR-based rule identifies many large outliers. The fraud target is highly imbalanced, with fraud accounting for only about 3.5% of transactions. Several categorical columns may require careful encoding or handling because they appear to have many unique values or sparse categories.

## Generated Outputs

The following files were generated:

- `reports/figures/top_missing_transaction_columns.png`
- `reports/figures/top_missing_identity_columns.png`
- `reports/model_reports/data_quality_summary.csv`
- `reports/model_reports/transaction_missing_values.csv`
- `reports/model_reports/identity_missing_values.csv`

## Data Quality Risks

The main data quality risks identified are:

- High missingness in several transaction and identity columns.
- Partial identity coverage because not all transactions have identity records.
- Severe fraud class imbalance.
- Skewed transaction amount distribution with large outliers.
- Possible high-cardinality categorical variables that require careful encoding.

## Conclusion

Before preprocessing and modelling, the pipeline should address missing values, decide how to handle sparse identity coverage, manage extreme transaction amounts, and account for the severe class imbalance so that the models are trained on a more reliable and representative dataset.
