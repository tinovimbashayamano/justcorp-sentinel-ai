from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt


DATA_DIR = Path("data/raw")
FIGURES_DIR = Path("reports/figures")
SUMMARY_DIR = Path("reports/model_reports")

TRAIN_TRANSACTION_FILE = DATA_DIR / "train_transaction.csv"
TRAIN_IDENTITY_FILE = DATA_DIR / "train_identity.csv"
EDA_SUMMARY_FILE = SUMMARY_DIR / "eda_summary.csv"


def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    train_transaction = pd.read_csv(TRAIN_TRANSACTION_FILE)
    train_identity = pd.read_csv(TRAIN_IDENTITY_FILE)

    return train_transaction, train_identity


def create_output_directories() -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    SUMMARY_DIR.mkdir(parents=True, exist_ok=True)


def summarise_dataset(
    train_transaction: pd.DataFrame,
    train_identity: pd.DataFrame,
) -> pd.DataFrame:
    fraud_counts = train_transaction["isFraud"].value_counts()
    fraud_percentages = train_transaction["isFraud"].value_counts(normalize=True) * 100

    summary_records = [
        {
            "metric": "train_transaction_rows",
            "value": train_transaction.shape[0],
        },
        {
            "metric": "train_transaction_columns",
            "value": train_transaction.shape[1],
        },
        {
            "metric": "train_identity_rows",
            "value": train_identity.shape[0],
        },
        {
            "metric": "train_identity_columns",
            "value": train_identity.shape[1],
        },
        {
            "metric": "non_fraud_count",
            "value": fraud_counts.get(0, 0),
        },
        {
            "metric": "fraud_count",
            "value": fraud_counts.get(1, 0),
        },
        {
            "metric": "non_fraud_percentage",
            "value": round(fraud_percentages.get(0, 0), 3),
        },
        {
            "metric": "fraud_percentage",
            "value": round(fraud_percentages.get(1, 0), 3),
        },
        {
            "metric": "transaction_missing_percentage_average",
            "value": round(train_transaction.isna().mean().mean() * 100, 3),
        },
        {
            "metric": "identity_missing_percentage_average",
            "value": round(train_identity.isna().mean().mean() * 100, 3),
        },
    ]

    return pd.DataFrame(summary_records)


def plot_fraud_distribution(train_transaction: pd.DataFrame) -> None:
    fraud_counts = train_transaction["isFraud"].value_counts().sort_index()

    plt.figure(figsize=(6, 4))
    fraud_counts.plot(kind="bar")
    plt.title("Fraud Class Distribution")
    plt.xlabel("Fraud Label")
    plt.ylabel("Number of Transactions")
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "fraud_distribution.png")
    plt.close()


def plot_transaction_amount_by_fraud(train_transaction: pd.DataFrame) -> None:
    amount_sample = train_transaction[["TransactionAmt", "isFraud"]].sample(n=50000, random_state=42)

    plt.figure(figsize=(8, 5))
    amount_sample.boxplot(column="TransactionAmt", by="isFraud")
    plt.title("Transaction Amount by Fraud Label")
    plt.suptitle("")
    plt.xlabel("Fraud Label")
    plt.ylabel("Transaction Amount")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "transaction_amount_by_fraud.png")
    plt.close()


def plot_product_code_distribution(train_transaction: pd.DataFrame) -> None:
    product_counts = train_transaction["ProductCD"].value_counts()

    plt.figure(figsize=(7, 4))
    product_counts.plot(kind="bar")
    plt.title("Product Code Distribution")
    plt.xlabel("Product Code")
    plt.ylabel("Number of Transactions")
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "product_code_distribution.png")
    plt.close()


def print_basic_observations(
    train_transaction: pd.DataFrame,
    train_identity: pd.DataFrame,
    eda_summary: pd.DataFrame,
) -> None:
    print("Initial EDA Summary")
    print("=" * 80)
    print(eda_summary)
    print()

    print("Transaction amount description:")
    print(train_transaction["TransactionAmt"].describe())
    print()

    print("ProductCD distribution:")
    print(train_transaction["ProductCD"].value_counts())
    print()

    print("Top 10 columns with highest missing values in train_transaction:")
    print((train_transaction.isna().mean() * 100).sort_values(ascending=False).head(10))
    print()

    print("Top 10 columns with highest missing values in train_identity:")
    print((train_identity.isna().mean() * 100).sort_values(ascending=False).head(10))


def main() -> None:
    create_output_directories()

    train_transaction, train_identity = load_data()

    eda_summary = summarise_dataset(train_transaction, train_identity)
    eda_summary.to_csv(EDA_SUMMARY_FILE, index=False)

    plot_fraud_distribution(train_transaction)
    plot_transaction_amount_by_fraud(train_transaction)
    plot_product_code_distribution(train_transaction)

    print_basic_observations(train_transaction, train_identity, eda_summary)

    print()
    print(f"EDA summary saved to: {EDA_SUMMARY_FILE}")
    print(f"Figures saved to: {FIGURES_DIR}")


if __name__ == "__main__":
    main()
