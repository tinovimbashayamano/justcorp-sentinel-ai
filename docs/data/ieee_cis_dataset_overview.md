# IEEE-CIS Fraud Detection — Dataset Overview

This document summarizes the IEEE-CIS Fraud Detection dataset layout and contents used in this project.

Dataset source
- Public Kaggle competition: IEEE-CIS Fraud Detection (transaction + identity tables).

Files included
- `train_transaction.csv` — training transactions with target `isFraud`.
- `train_identity.csv` — additional identity features for training transactions.
- `test_transaction.csv` — test transactions (no `isFraud` column).
- `test_identity.csv` — identity features for test transactions.
- `sample_submission.csv` — example submission format.

Notes
- Transactions and identity tables can be merged on `TransactionID` for feature engineering.
- Some features are anonymized (V columns); many columns have missing values and require careful preprocessing.
- The target is highly imbalanced; use stratified sampling or appropriate evaluation metrics (AUC, precision-recall).

Suggested usage
- Store raw CSVs under `data/raw/ieee-fraud-detection/`.
- Use `ml/src/data/inspect_ieee_dataset.py` to quickly inspect file sizes and target distribution.

References
- Original competition on Kaggle: https://www.kaggle.com/competitions/ieee-fraud-detection
