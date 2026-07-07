# Feature Engineering Strategy

## Objective
This document describes the planned feature engineering strategy for the IEEE-CIS fraud detection dataset used in the JustCorp Sentinel AI project.

## Feature Engineering Principles
The feature engineering process must be reproducible, explainable, and suitable for a fraud detection pipeline. Features should be created in a way that supports model performance without introducing data leakage.

## Candidate Feature Groups

### 1. Transaction Amount Features
`TransactionAmt` will be retained as an important numerical feature. Because transaction amounts are strongly right-skewed, a log-transformed version called `TransactionAmt_log` will also be considered using `log1p(TransactionAmt)`.

### 2. Transaction Time Features
`TransactionDT` is a time delta from a reference point. It will be used to derive time-based features such as:

- `transaction_hour`
- `transaction_day`
These features may help capture timing patterns related to fraud.

### 3. Product Code Features
`ProductCD` will be treated as a categorical feature. EDA showed that product codes are unevenly distributed, so the model may benefit from learning fraud patterns associated with different product codes.

### 4. Card and Address Features
Card-related columns such as `card1` to `card6` and address columns such as `addr1` and `addr2` will be retained. Additional missingness-count features such as `card_missing_count` and `address_missing_count` may help represent incomplete transaction information.

### 5. Email Domain Features
`P_emaildomain` and `R_emaildomain` will be treated as categorical features. Missingness indicators and an `email_domain_match` feature may be useful because differences between purchaser and recipient email domains may contain fraud-related signals.

### 6. Identity Coverage Features
Because only some transactions have matching identity records, a `has_identity` feature will be created. This feature indicates whether a transaction has associated identity or device data.

### 7. Missingness Features
The dataset contains substantial missing values. Missingness itself may carry useful fraud signals, so selected missingness indicators may be created instead of only imputing values.

### 8. Anonymous Engineered Features
Anonymous features such as `C`, `D`, `M`, and `V` columns will be handled carefully. Their exact business meanings are not known, but they may still contain predictive information. Feature selection will later help decide which of these features are most useful.

## Features to Avoid
The target variable `isFraud` must never be used as an input feature. `sample_submission.csv` must not be treated as labelled data. Preprocessing must be fitted only on the training split to avoid data leakage.

## Encoding Strategy
Low-cardinality categorical features may be one-hot encoded. High-cardinality categorical features such as `DeviceInfo`, `id_31`, and `id_33` require careful handling because naive one-hot encoding may create too many sparse columns.

## Missing-Value Strategy
Columns with moderate missingness may be imputed. Columns with extremely high missingness may be dropped or converted into missingness indicators depending on their usefulness. This decision will be refined during preprocessing and feature selection.

## Class Imbalance Consideration
The dataset is highly imbalanced, with fraud cases representing a small minority of transactions. Feature engineering alone will not solve imbalance, so later modelling steps must use suitable evaluation metrics and imbalance-handling strategies.

## Generated Outputs
The feature engineering candidate analysis generates the following outputs:

- `reports/figures/transaction_amount_log_distribution.png`
- `reports/figures/fraud_rate_by_product_code.png`
- `reports/figures/identity_coverage_by_fraud.png`
- `reports/figures/fraud_rate_by_transaction_hour.png`
- `reports/model_reports/feature_engineering_candidate_summary.csv`

## Conclusion
The feature engineering strategy will focus on amount transformations, time-derived features, categorical encoding, identity coverage indicators, missingness indicators, and careful handling of anonymised high-dimensional features. These steps will prepare the dataset for robust preprocessing, feature selection, and fraud detection modelling.
