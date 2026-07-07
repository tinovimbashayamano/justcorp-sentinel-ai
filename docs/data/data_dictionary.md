# Data Dictionary

## Dataset Name
IEEE-CIS Fraud Detection Dataset

## Dataset Purpose
The dataset is used to support the development of a machine learning fraud detection model for identifying potentially fraudulent financial transactions.

## Main Training Files
- `train_transaction.csv`: Main training transaction dataset containing transaction-level features and the target variable `isFraud`.
- `train_identity.csv`: Additional identity and device-related information for some transactions in the training dataset.

## Key Identifier
- `TransactionID`: Unique transaction identifier used to link transaction records with identity records.

## Target Variable
- `isFraud`: Target variable for supervised learning. A value of `0` represents a non-fraud transaction, while `1` represents a fraud transaction.

## Important Transaction Columns
- `TransactionDT`: Time delta from a reference point. It is not a real calendar date but can help represent transaction timing.
- `TransactionAmt`: Transaction amount. This is an important feature because unusual transaction values may indicate suspicious activity.
- `ProductCD`: Product code associated with the transaction.
- `card1`–`card6`: Card-related transaction features. These are anonymized but may represent card type, category, or issuer-related information.
- `addr1`, `addr2`: Address-related features. These may help represent location or billing-related patterns.
- `P_emaildomain`: Purchaser email domain.
- `R_emaildomain`: Recipient email domain.

## Engineered and Anonymous Transaction Features
- `C1`–`C14`: Count-like engineered features. These may represent frequency or grouped transaction behaviour.
- `D1`–`D15`: Time-distance or date-difference style features. These may represent time gaps or transaction history behaviour.
- `M1`–`M9`: Match or boolean-like features. These may represent whether certain transaction attributes match.
- `V1`–`V339`: Anonymous engineered transaction features. Their exact business meanings are not disclosed, but they may still be useful for fraud detection.

## Identity and Device Features
- `id_01` onward: Identity-related and device-related features connected to some transactions.
- `DeviceType`: Device category used during the transaction, where available.
- `DeviceInfo`: Additional device information, where available.

## Notes on Anonymised Features
Many columns in the IEEE-CIS dataset are anonymised. This means their exact real-world meanings are not publicly disclosed. In this project, these features will be analysed statistically and used carefully during feature engineering, model training, and explainability.

## Notes on Missing Values
The identity dataset has fewer rows than the transaction dataset, meaning identity and device information is not available for every transaction. Missing values will need to be analysed before preprocessing and model training.

## Notes on Class Imbalance
The training dataset is highly imbalanced. Only a small percentage of transactions are labelled as fraud. This means model evaluation must not rely on accuracy alone. Later stages should consider metrics such as precision, recall, F1-score, ROC-AUC, and PR-AUC.

## Generated Dictionary
A generated column-level dictionary is stored in:

`docs/data/data_dictionary_generated.csv`

This file contains sampled data types, column groups, missing-value percentages from a sample, and example values.
