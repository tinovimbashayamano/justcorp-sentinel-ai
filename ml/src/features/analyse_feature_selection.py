from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt


DATA_DIR = Path("data/raw")
FIGURES_DIR = Path("reports/figures")
SUMMARY_DIR = Path("reports/model_reports")

TRAIN_TRANSACTION_FILE = DATA_DIR / "train_transaction.csv"
TRAIN_IDENTITY_FILE = DATA_DIR / "train_identity.csv"

FEATURE_SELECTION_SUMMARY_FILE = SUMMARY_DIR / "feature_selection_summary.csv"
FEATURE_MISSINGNESS_FILE = SUMMARY_DIR / "feature_missingness_summary.csv"
NUMERIC_CORRELATION_FILE = SUMMARY_DIR / "numeric_correlations_with_fraud.csv"


def create_output_directories() -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    SUMMARY_DIR.mkdir(parents=True, exist_ok=True)


def classify_column(column_name: str) -> str:
    if column_name == "TransactionID":
        return "identifier"
    if column_name == "isFraud":
        return "target"
    if column_name == "TransactionDT":
        return "time"
    if column_name == "TransactionAmt":
        return "amount"
    if column_name == "ProductCD":
        return "product"
    if column_name in ["DeviceType", "DeviceInfo"]:
        return "identity_device_feature"
    if column_name.startswith("card"):
        return "card_feature"
    if column_name.startswith("addr"):
        return "address_feature"
    if column_name.startswith("dist"):
        return "distance_feature"
    if column_name in ["P_emaildomain", "R_emaildomain"]:
        return "email_domain"
    if column_name.startswith("C"):
        return "count_feature"
    if column_name.startswith("D"):
        return "time_delta_feature"
    if column_name.startswith("M"):
        return "match_feature"
    if column_name.startswith("V"):
        return "anonymous_transaction_feature"
    if column_name.startswith("id_") or column_name.startswith("id-"):
        return "identity_feature"
    return "other"


def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    train_transaction = pd.read_csv(TRAIN_TRANSACTION_FILE)
    train_identity = pd.read_csv(TRAIN_IDENTITY_FILE)

    return train_transaction, train_identity


def merge_training_data(
    train_transaction: pd.DataFrame,
    train_identity: pd.DataFrame,
) -> pd.DataFrame:
    merged_df = train_transaction.merge(
        train_identity,
        on="TransactionID",
        how="left",
    )

    return merged_df


def calculate_feature_missingness(df: pd.DataFrame) -> pd.DataFrame:
    records = []

    for column in df.columns:
        records.append(
            {
                "column_name": column,
                "column_group": classify_column(column),
                "missing_percentage": round(df[column].isna().mean() * 100, 3),
                "unique_values": df[column].nunique(dropna=True),
                "data_type": str(df[column].dtype),
            }
        )

    return pd.DataFrame(records)


def identify_near_constant_columns(
    df: pd.DataFrame,
    threshold: float = 0.99,
) -> list[str]:
    near_constant_columns = []

    for column in df.columns:
        top_frequency = df[column].value_counts(dropna=False, normalize=True).head(1)

        if not top_frequency.empty and top_frequency.iloc[0] >= threshold:
            near_constant_columns.append(column)

    return near_constant_columns


def calculate_numeric_correlations(df: pd.DataFrame) -> pd.DataFrame:
    numeric_df = df.select_dtypes(include=["number"])

    correlations = numeric_df.corr(numeric_only=True)["isFraud"].drop(
        labels=["isFraud"],
        errors="ignore",
    )

    correlation_df = (
        correlations.abs()
        .sort_values(ascending=False)
        .reset_index()
        .rename(columns={"index": "feature_name", "isFraud": "absolute_correlation"})
    )

    signed_correlations = correlations.reindex(correlation_df["feature_name"]).values
    correlation_df["signed_correlation"] = signed_correlations

    return correlation_df


def create_feature_selection_summary(
    missingness_df: pd.DataFrame,
    near_constant_columns: list[str],
) -> pd.DataFrame:
    summary = (
        missingness_df.groupby("column_group")
        .agg(
            feature_count=("column_name", "count"),
            average_missing_percentage=("missing_percentage", "mean"),
            max_missing_percentage=("missing_percentage", "max"),
            average_unique_values=("unique_values", "mean"),
        )
        .reset_index()
    )

    summary["average_missing_percentage"] = summary[
        "average_missing_percentage"
    ].round(3)
    summary["max_missing_percentage"] = summary["max_missing_percentage"].round(3)
    summary["average_unique_values"] = summary["average_unique_values"].round(3)

    summary["near_constant_columns_in_group"] = summary["column_group"].apply(
        lambda group: sum(
            missingness_df[
                (missingness_df["column_group"] == group)
                & (missingness_df["column_name"].isin(near_constant_columns))
            ].shape
        )
    )

    return summary.sort_values("feature_count", ascending=False)


def plot_top_numeric_correlations(correlation_df: pd.DataFrame) -> None:
    top_corr = correlation_df.head(20).sort_values("absolute_correlation")

    plt.figure(figsize=(10, 7))
    plt.barh(top_corr["feature_name"], top_corr["absolute_correlation"])
    plt.title("Top Numeric Correlations with Fraud Target")
    plt.xlabel("Absolute Correlation with isFraud")
    plt.ylabel("Feature")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "top_numeric_correlations_with_fraud.png")
    plt.close()


def plot_missingness_by_column_group(summary_df: pd.DataFrame) -> None:
    plot_df = summary_df.sort_values("average_missing_percentage")

    plt.figure(figsize=(10, 7))
    plt.barh(plot_df["column_group"], plot_df["average_missing_percentage"])
    plt.title("Average Missingness by Column Group")
    plt.xlabel("Average Missing Percentage")
    plt.ylabel("Column Group")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "missingness_by_column_group.png")
    plt.close()


def plot_selected_feature_group_summary(summary_df: pd.DataFrame) -> None:
    plot_df = summary_df.sort_values("feature_count")

    plt.figure(figsize=(10, 7))
    plt.barh(plot_df["column_group"], plot_df["feature_count"])
    plt.title("Feature Count by Column Group")
    plt.xlabel("Number of Features")
    plt.ylabel("Column Group")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "selected_feature_group_summary.png")
    plt.close()


def print_feature_selection_report(
    missingness_df: pd.DataFrame,
    correlation_df: pd.DataFrame,
    near_constant_columns: list[str],
    summary_df: pd.DataFrame,
) -> None:
    print("Feature Selection Analysis")
    print("=" * 80)

    print("Column group summary:")
    print(summary_df)
    print()

    print("Top 20 numeric correlations with isFraud:")
    print(correlation_df.head(20))
    print()

    print(f"Near-constant columns count: {len(near_constant_columns)}")
    print("First 20 near-constant columns:")
    print(near_constant_columns[:20])
    print()

    print("Columns with 90% or more missing values:")
    high_missing = missingness_df[missingness_df["missing_percentage"] >= 90]
    print(high_missing[["column_name", "column_group", "missing_percentage"]])


def main() -> None:
    create_output_directories()

    train_transaction, train_identity = load_data()
    merged_df = merge_training_data(train_transaction, train_identity)

    missingness_df = calculate_feature_missingness(merged_df)
    near_constant_columns = identify_near_constant_columns(merged_df)
    correlation_df = calculate_numeric_correlations(merged_df)
    summary_df = create_feature_selection_summary(
        missingness_df,
        near_constant_columns,
    )

    missingness_df.to_csv(FEATURE_MISSINGNESS_FILE, index=False)
    correlation_df.to_csv(NUMERIC_CORRELATION_FILE, index=False)
    summary_df.to_csv(FEATURE_SELECTION_SUMMARY_FILE, index=False)

    plot_top_numeric_correlations(correlation_df)
    plot_missingness_by_column_group(summary_df)
    plot_selected_feature_group_summary(summary_df)

    print_feature_selection_report(
        missingness_df,
        correlation_df,
        near_constant_columns,
        summary_df,
    )

    print()
    print(f"Feature missingness saved to: {FEATURE_MISSINGNESS_FILE}")
    print(f"Numeric correlations saved to: {NUMERIC_CORRELATION_FILE}")
    print(f"Feature selection summary saved to: {FEATURE_SELECTION_SUMMARY_FILE}")
    print(f"Figures saved to: {FIGURES_DIR}")


if __name__ == "__main__":
    main()
