from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


DATA_DIR = Path("data/raw")
FIGURES_DIR = Path("reports/figures")
SUMMARY_DIR = Path("reports/model_reports")

TRAIN_TRANSACTION_FILE = DATA_DIR / "train_transaction.csv"
TRAIN_IDENTITY_FILE = DATA_DIR / "train_identity.csv"

FEATURE_STRATEGY_SUMMARY_FILE = SUMMARY_DIR / "feature_engineering_candidate_summary.csv"


def create_output_directories() -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    SUMMARY_DIR.mkdir(parents=True, exist_ok=True)


def load_selected_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    transaction_columns = [
        "TransactionID",
        "isFraud",
        "TransactionDT",
        "TransactionAmt",
        "ProductCD",
        "card1",
        "card2",
        "card3",
        "card4",
        "card5",
        "card6",
        "addr1",
        "addr2",
        "P_emaildomain",
        "R_emaildomain",
    ]

    identity_columns = [
        "TransactionID",
        "DeviceType",
        "DeviceInfo",
    ]

    train_transaction = pd.read_csv(
        TRAIN_TRANSACTION_FILE,
        usecols=transaction_columns,
    )

    train_identity = pd.read_csv(
        TRAIN_IDENTITY_FILE,
        usecols=identity_columns,
    )

    return train_transaction, train_identity


def build_candidate_features(
    train_transaction: pd.DataFrame,
    train_identity: pd.DataFrame,
) -> pd.DataFrame:
    df = train_transaction.copy()

    identity_ids = set(train_identity["TransactionID"])

    df["transaction_hour"] = (df["TransactionDT"] // 3600) % 24
    df["transaction_day"] = df["TransactionDT"] // 86400
    df["TransactionAmt_log"] = np.log1p(df["TransactionAmt"])

    df["has_identity"] = df["TransactionID"].isin(identity_ids).astype(int)

    df["P_emaildomain_missing"] = df["P_emaildomain"].isna().astype(int)
    df["R_emaildomain_missing"] = df["R_emaildomain"].isna().astype(int)

    df["email_domain_match"] = np.where(
        df["P_emaildomain"].notna() & df["R_emaildomain"].notna(),
        (df["P_emaildomain"] == df["R_emaildomain"]).astype(int),
        -1,
    )

    card_columns = ["card1", "card2", "card3", "card4", "card5", "card6"]
    df["card_missing_count"] = df[card_columns].isna().sum(axis=1)

    address_columns = ["addr1", "addr2"]
    df["address_missing_count"] = df[address_columns].isna().sum(axis=1)

    return df


def summarise_candidate_features(df: pd.DataFrame) -> pd.DataFrame:
    candidate_columns = [
        "TransactionAmt",
        "TransactionAmt_log",
        "transaction_hour",
        "transaction_day",
        "ProductCD",
        "has_identity",
        "P_emaildomain_missing",
        "R_emaildomain_missing",
        "email_domain_match",
        "card_missing_count",
        "address_missing_count",
    ]

    records = []

    for column in candidate_columns:
        records.append(
            {
                "feature_name": column,
                "data_type": str(df[column].dtype),
                "missing_percentage": round(df[column].isna().mean() * 100, 3),
                "unique_values": df[column].nunique(dropna=True),
                "example_values": df[column].dropna().astype(str).head(5).tolist(),
            }
        )

    return pd.DataFrame(records)


def plot_transaction_amount_log_distribution(df: pd.DataFrame) -> None:
    sample_size = min(100000, len(df))
    sample_df = df.sample(n=sample_size, random_state=42)

    plt.figure(figsize=(8, 5))
    sample_df["TransactionAmt_log"].plot(kind="hist", bins=50)
    plt.title("Log-Transformed Transaction Amount Distribution")
    plt.xlabel("log1p(TransactionAmt)")
    plt.ylabel("Frequency")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "transaction_amount_log_distribution.png")
    plt.close()


def plot_fraud_rate_by_product_code(df: pd.DataFrame) -> None:
    fraud_rate = df.groupby("ProductCD")["isFraud"].mean().sort_values() * 100

    plt.figure(figsize=(7, 4))
    fraud_rate.plot(kind="bar")
    plt.title("Fraud Rate by Product Code")
    plt.xlabel("Product Code")
    plt.ylabel("Fraud Rate (%)")
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "fraud_rate_by_product_code.png")
    plt.close()


def plot_identity_coverage_by_fraud(df: pd.DataFrame) -> None:
    coverage = df.groupby("isFraud")["has_identity"].mean() * 100

    plt.figure(figsize=(6, 4))
    coverage.plot(kind="bar")
    plt.title("Identity Coverage by Fraud Label")
    plt.xlabel("Fraud Label")
    plt.ylabel("Transactions with Identity Data (%)")
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "identity_coverage_by_fraud.png")
    plt.close()


def plot_fraud_rate_by_transaction_hour(df: pd.DataFrame) -> None:
    fraud_rate = df.groupby("transaction_hour")["isFraud"].mean() * 100

    plt.figure(figsize=(9, 4))
    fraud_rate.plot(kind="bar")
    plt.title("Fraud Rate by Derived Transaction Hour")
    plt.xlabel("Derived Transaction Hour")
    plt.ylabel("Fraud Rate (%)")
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "fraud_rate_by_transaction_hour.png")
    plt.close()


def print_feature_observations(df: pd.DataFrame, summary: pd.DataFrame) -> None:
    print("Feature Engineering Candidate Summary")
    print("=" * 80)
    print(summary)
    print()

    print("Fraud rate by ProductCD (%):")
    print((df.groupby("ProductCD")["isFraud"].mean() * 100).sort_values(ascending=False))
    print()

    print("Identity coverage by fraud label (%):")
    print((df.groupby("isFraud")["has_identity"].mean() * 100))
    print()

    print("Fraud rate by email domain match flag (%):")
    print((df.groupby("email_domain_match")["isFraud"].mean() * 100))
    print()

    print("Transaction amount comparison:")
    print(df[["TransactionAmt", "TransactionAmt_log"]].describe())


def main() -> None:
    create_output_directories()

    train_transaction, train_identity = load_selected_data()
    feature_df = build_candidate_features(train_transaction, train_identity)

    summary = summarise_candidate_features(feature_df)
    summary.to_csv(FEATURE_STRATEGY_SUMMARY_FILE, index=False)

    plot_transaction_amount_log_distribution(feature_df)
    plot_fraud_rate_by_product_code(feature_df)
    plot_identity_coverage_by_fraud(feature_df)
    plot_fraud_rate_by_transaction_hour(feature_df)

    print_feature_observations(feature_df, summary)

    print()
    print(f"Feature strategy summary saved to: {FEATURE_STRATEGY_SUMMARY_FILE}")
    print(f"Figures saved to: {FIGURES_DIR}")


if __name__ == "__main__":
    main()
