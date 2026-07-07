# Initial Exploratory Data Analysis Report

## Objective

This report summarises the initial exploratory data analysis performed on the IEEE-CIS fraud detection dataset.

## Dataset Shape

| Dataset | Rows | Columns |
|---|---:|---:|
| train_transaction.csv | 590,540 | 394 |
| train_identity.csv | 144,233 | 41 |

## Target Distribution

| Class | Meaning | Count | Percentage |
|---|---|---:|---:|
| 0 | Non-fraud | 569,877 | 96.501% |
| 1 | Fraud | 20,663 | 3.499% |

## Initial Observations

The dataset is highly imbalanced, with fraud cases accounting for only about 3.5% of transactions. This means the target distribution is strongly skewed and any model should be evaluated with metrics that account for class imbalance.

Not every transaction appears to have identity information available. The transaction table contains far more rows than the identity table, which suggests that a substantial portion of transactions do not have matching identity records. That makes the identity features sparse and potentially less reliable for some rows.

The transaction amount distribution is right-skewed, with a long tail of relatively large values. Fraudulent transactions tend to have higher and more variable amounts than non-fraudulent ones, although the distribution is still dominated by low-value transactions.

The product code distribution is concentrated around a few common codes, with ProductCD values such as W and C appearing most often. This suggests that product type is a useful categorical feature, but it may be unevenly distributed across the dataset.

Missing values appear to be important because the data contains a large amount of missingness, especially in the identity features. The high percentage of missing values may reduce the usefulness of some columns unless they are carefully imputed or handled during preprocessing.

## Generated EDA Outputs

The following EDA figures were generated:

- `reports/figures/fraud_distribution.png`
- `reports/figures/transaction_amount_by_fraud.png`
- `reports/figures/product_code_distribution.png`

The EDA summary file was generated at:

- `reports/model_reports/eda_summary.csv`

## Conclusion

The EDA suggests that the dataset is suitable for fraud detection modeling, but it requires careful preprocessing because of severe class imbalance, sparse identity coverage, skewed transaction amounts, and substantial missing values. These characteristics indicate that feature engineering and robust validation will be important before model training.
