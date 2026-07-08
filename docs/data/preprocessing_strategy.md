# Preprocessing Strategy

## Objective

This document explains the preprocessing strategy used to create the baseline modelling dataset for the IEEE-CIS fraud detection data.

## Purpose

The purpose of preprocessing is to convert raw transaction and identity data into a cleaner feature dataset that can later be used for model training and evaluation.

## Dataset Used

The preprocessing script uses selected columns from:

- `train_transaction.csv`
- `train_identity.csv`

The generated dataset is saved locally as:

- `data/processed/baseline_modeling_dataset.csv.gz`

This processed dataset is not committed to GitHub because it is a generated data file.

## Feature Groups Included

The baseline dataset includes:

- Transaction amount features
- Product code
- Card features
- Address features
- Email-domain features
- Count features
- Time-delta features
- Match features
- Selected high-signal anonymous `V` features
- Selected identity and device features

## Engineered Features

The following engineered features are created:

- `TransactionAmt_log`
- `transaction_hour`
- `transaction_day`
- `has_identity`
- `P_emaildomain_missing`
- `R_emaildomain_missing`
- `email_domain_match`
- `card_missing_count`
- `address_missing_count`

## Leakage Prevention

`TransactionID` is excluded from model training because it is only an identifier.

`isFraud` is kept only as the target variable and is not used as an input feature.

`TransactionDT` is not used directly in the baseline feature dataset. Instead, derived time features are created from it.

## Missing-Value Handling

Columns with 90% or more missing values are dropped from the baseline dataset.

Remaining numerical missing values are filled using the median value of each feature.

Remaining categorical missing values are filled with the value `missing`.

## Near-Constant Feature Handling

Near-constant columns are removed using a 99% dominance threshold. This means a feature is dropped if one value appears in at least 99% of rows.

## Categorical Feature Handling

Categorical values are kept as text at this stage. Rare categories are grouped into `rare` to reduce sparsity.

Final encoding will be handled later inside the modelling pipeline.

## Output

The script generates:

- `data/processed/baseline_modeling_dataset.csv.gz`
- `reports/model_reports/baseline_feature_dataset_summary.csv`

## Conclusion

This preprocessing stage creates a clean baseline dataset while preventing leakage, reducing extreme missingness, removing near-constant features, and preserving useful fraud-related signals for later modelling.
