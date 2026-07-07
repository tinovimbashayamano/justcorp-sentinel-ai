from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt


DATA_DIR = Path("data/raw")
FIGURES_DIR = Path("reports/figures")
SUMMARY_DIR = Path("reports/model_reports")

TRAIN_TRANSACTION_FILE = DATA_DIR / "train_transaction.csv"
TRAIN_IDENTITY_FILE = DATA_DIR / "train_identity.csv"

QUALITY_SUMMARY_FILE = SUMMARY_DIR / "data_quality_summary.csv"
TRANSACTION_MISSING_FILE = SUMMARY_DIR / "transaction_missing_values.csv"
IDENTITY_MISSING_FILE = SUMMARY_DIR / "identity_missing_values.csv"


def create_output_directories() -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    SUMMARY_DIR.mkdir(parents=True, exist_ok=True)


def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    train_transaction = pd.read_csv(TRAIN_TRANSACTION_FILE)
    train_identity = pd.read_csv(TRAIN_IDENTITY_FILE)
    return train_transaction, train_identity


def calculate_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    missing_count = df.isna().sum()
    missing_percentage = df.isna().mean() * 100

    missing_df = pd.DataFrame(
        {
            "column_name": df.columns,
            "missing_count": missing_count.values,
            "missing_percentage": missing_percentage.values,
        }
    )

    return missing_df.sort_values("missing_percentage", ascending=False)


def plot_top_missing_values(
    missing_df: pd.DataFrame,
    title: str,
    output_file: Path,
    top_n: int = 20,
) -> None:
    top_missing = missing_df.head(top_n).sort_values("missing_percentage")

    plt.figure(figsize=(10, 7))
    plt.barh(top_missing["column_name"], top_missing["missing_percentage"])
    plt.title(title)
    plt.xlabel("Missing Percentage")
    plt.ylabel("Column")
    plt.tight_layout()
    plt.savefig(output_file)
    plt.close()


def count_near_constant_columns(df: pd.DataFrame, threshold: float = 0.99) -> int:
    near_constant_count = 0

    for column in df.columns:
        top_frequency = df[column].value_counts(dropna=False, normalize=True).head(1)
        if not top_frequency.empty and top_frequency.iloc[0] >= threshold:
            near_constant_count += 1

    return near_constant_count


def get_high_cardinality_columns(df: pd.DataFrame, threshold: int = 100) -> list[str]:
    object_columns = df.select_dtypes(include=["object"]).columns

    high_cardinality_columns = []

    for column in object_columns:
        unique_count = df[column].nunique(dropna=True)
        if unique_count > threshold:
            high_cardinality_columns.append(column)

    return high_cardinality_columns


def assess_data_quality(
    train_transaction: pd.DataFrame,
    train_identity: pd.DataFrame,
) -> pd.DataFrame:
    transaction_duplicate_ids = train_transaction["TransactionID"].duplicated().sum()
    identity_duplicate_ids = train_identity["TransactionID"].duplicated().sum()

    identity_ids = set(train_identity["TransactionID"])
    transaction_ids = set(train_transaction["TransactionID"])
    matched_identity_count = len(transaction_ids.intersection(identity_ids))
    identity_coverage_percentage = (matched_identity_count / len(train_transaction)) * 100

    fraud_percentage = train_transaction["isFraud"].mean() * 100

    non_positive_amount_count = (train_transaction["TransactionAmt"] <= 0).sum()

    amount_q1 = train_transaction["TransactionAmt"].quantile(0.25)
    amount_q3 = train_transaction["TransactionAmt"].quantile(0.75)
    amount_iqr = amount_q3 - amount_q1
    amount_upper_bound = amount_q3 + (1.5 * amount_iqr)
    amount_outlier_count = (train_transaction["TransactionAmt"] > amount_upper_bound).sum()

    transaction_near_constant_count = count_near_constant_columns(train_transaction)
    identity_near_constant_count = count_near_constant_columns(train_identity)

    transaction_high_cardinality = get_high_cardinality_columns(train_transaction)
    identity_high_cardinality = get_high_cardinality_columns(train_identity)

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
            "metric": "transaction_duplicate_transaction_ids",
            "value": transaction_duplicate_ids,
        },
        {
            "metric": "identity_duplicate_transaction_ids",
            "value": identity_duplicate_ids,
        },
        {
            "metric": "matched_identity_records",
            "value": matched_identity_count,
        },
        {
            "metric": "identity_coverage_percentage",
            "value": round(identity_coverage_percentage, 3),
        },
        {
            "metric": "fraud_percentage",
            "value": round(fraud_percentage, 3),
        },
        {
            "metric": "transaction_average_missing_percentage",
            "value": round(train_transaction.isna().mean().mean() * 100, 3),
        },
        {
            "metric": "identity_average_missing_percentage",
            "value": round(train_identity.isna().mean().mean() * 100, 3),
        },
        {
            "metric": "non_positive_transaction_amount_count",
            "value": non_positive_amount_count,
        },
        {
            "metric": "transaction_amount_iqr_upper_bound",
            "value": round(amount_upper_bound, 3),
        },
        {
            "metric": "transaction_amount_outlier_count_iqr_rule",
            "value": amount_outlier_count,
        },
        {
            "metric": "transaction_near_constant_columns_99_percent",
            "value": transaction_near_constant_count,
        },
        {
            "metric": "identity_near_constant_columns_99_percent",
            "value": identity_near_constant_count,
        },
        {
            "metric": "transaction_high_cardinality_object_columns",
            "value": ", ".join(transaction_high_cardinality)
            if transaction_high_cardinality
            else "None",
        },
        {
            "metric": "identity_high_cardinality_object_columns",
            "value": ", ".join(identity_high_cardinality)
            if identity_high_cardinality
            else "None",
        },
    ]

    return pd.DataFrame(summary_records)


def print_report(
    quality_summary: pd.DataFrame,
    transaction_missing: pd.DataFrame,
    identity_missing: pd.DataFrame,
) -> None:
    print("Data Quality Assessment Summary")
    print("=" * 80)
    print(quality_summary)
    print()

    print("Top 15 missing columns in train_transaction:")
    print(transaction_missing.head(15))
    print()

    print("Top 15 missing columns in train_identity:")
    print(identity_missing.head(15))
    print()


def main() -> None:
    create_output_directories()

    train_transaction, train_identity = load_data()

    transaction_missing = calculate_missing_values(train_transaction)
    identity_missing = calculate_missing_values(train_identity)

    transaction_missing.to_csv(TRANSACTION_MISSING_FILE, index=False)
    identity_missing.to_csv(IDENTITY_MISSING_FILE, index=False)

    plot_top_missing_values(
        transaction_missing,
        "Top Missing Columns in train_transaction",
        FIGURES_DIR / "top_missing_transaction_columns.png",
    )

    plot_top_missing_values(
        identity_missing,
        "Top Missing Columns in train_identity",
        FIGURES_DIR / "top_missing_identity_columns.png",
    )

    quality_summary = assess_data_quality(train_transaction, train_identity)
    quality_summary.to_csv(QUALITY_SUMMARY_FILE, index=False)

    print_report(quality_summary, transaction_missing, identity_missing)

    print(f"Quality summary saved to: {QUALITY_SUMMARY_FILE}")
    print(f"Transaction missing values saved to: {TRANSACTION_MISSING_FILE}")
    print(f"Identity missing values saved to: {IDENTITY_MISSING_FILE}")
    print(f"Figures saved to: {FIGURES_DIR}")


if __name__ == "__main__":
    main()
