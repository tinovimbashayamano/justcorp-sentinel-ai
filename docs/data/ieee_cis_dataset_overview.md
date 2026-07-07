# IEEE-CIS Fraud Detection — Dataset Overview

# IEEE-CIS Fraud Detection Dataset Overview

## Dataset Purpose

The IEEE-CIS fraud detection dataset is used to develop a machine learning model for identifying potentially fraudulent financial transactions. In this project, the dataset will support the development of the JustCorp Sentinel AI fraud detection engine.

## Files Identified

| File                  | Purpose                                                 |    Rows | Columns |
| --------------------- | ------------------------------------------------------- | ------: | ------: |
| train_transaction.csv | Training transaction data with fraud labels             | 590,540 |     394 |
| train_identity.csv    | Identity and device data for some training transactions | 144,233 |      41 |
| test_transaction.csv  | Test transaction data without fraud labels              | 506,691 |     393 |
| test_identity.csv     | Identity and device data for some test transactions     | 141,907 |      41 |
| sample_submission.csv | Kaggle submission format example                        | 506,691 |       2 |

## Target Variable

The target variable is `isFraud`.

* `0` means the transaction is not labelled as fraud.
* `1` means the transaction is labelled as fraud.

The target variable appears in `train_transaction.csv`.

## Key Identifier

The key identifier is `TransactionID`.

This column links transaction records with identity records. It is used to connect `train_transaction.csv` with `train_identity.csv`, and `test_transaction.csv` with `test_identity.csv`.

## Initial Target Distribution

The training transaction dataset contains:

| Class | Meaning               |   Count | Percentage |
| ----- | --------------------- | ------: | ---------: |
| 0     | Non-fraud transaction | 569,877 |    96.501% |
| 1     | Fraud transaction     |  20,663 |     3.499% |

## Initial Observations

The dataset is large, with 590,540 labelled training transactions and 394 transaction-related columns. The target variable is highly imbalanced because only 3.499% of the training transactions are labelled as fraud.

The `train_identity.csv` file has fewer rows than `train_transaction.csv`, which means identity and device information is only available for some transactions. This will need to be handled carefully during merging and missing-value analysis.

The `test_transaction.csv` file does not contain the `isFraud` target column because it is intended for prediction. The `sample_submission.csv` file contains placeholder values and should not be treated as a labelled target dataset.

Raw data is currently stored in `data/raw/` and must not be committed to GitHub.

## Data Engineering Notes

* Raw data should remain in `data/raw/`.
* Raw data should not be committed to GitHub.
* `TransactionID` will be used as the merge key.
* `train_transaction.csv` contains the supervised learning target.
* `train_identity.csv` contains additional identity and device features for some transactions.
* Missing values will be analysed in a later step.
* Class imbalance will be handled in a later step.


References
- Original competition on Kaggle: https://www.kaggle.com/competitions/ieee-fraud-detection
