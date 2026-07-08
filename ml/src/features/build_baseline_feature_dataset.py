from pathlib import Path

import numpy as np
import pandas as pd


DATA_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
SUMMARY_DIR = Path("reports/model_reports")

TRAIN_TRANSACTION_FILE = DATA_DIR / "train_transaction.csv"
TRAIN_IDENTITY_FILE = DATA_DIR / "train_identity.csv"

OUTPUT_DATASET_FILE = PROCESSED_DIR / "baseline_modeling_dataset.csv.gz"
SUMMARY_FILE = SUMMARY_DIR / "baseline_feature_dataset_summary.csv"

HIGH_MISSING_THRESHOLD = 90.0
NEAR_CONSTANT_THRESHOLD = 0.99
RARE_CATEGORY_MIN_COUNT = 1000

TOP_V_FEATURES = [
    "V257",
    "V246",
    "V244",
    "V242",
    "V201",
    "V200",
    "V189",
    "V188",
    "V45",
    "V258",
    "V158",
    "V156",
    "V149",
    "V44",
    "V228",
    "V87",
    "V86",
    "V147",
    "V170",
    "V52",
]


def create_output_directories() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    SUMMARY_DIR.mkdir(parents=True, exist_ok=True)


def get_transaction_columns() -> list[str]:
    base_columns = [
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

    count_columns = [f"C{i}" for i in range(1, 15)]
    time_delta_columns = [f"D{i}" for i in range(1, 16)]
    match_columns = [f"M{i}" for i in range(1, 10)]

    return base_columns + count_columns + time_delta_columns + match_columns + TOP_V_FEATURES


def get_identity_columns() -> list[str]:
    return [
        "TransactionID",
        "DeviceType",
        "DeviceInfo",
        "id_31",
        "id_33",
    ]


def load_selected_raw_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    train_transaction = pd.read_csv(
        TRAIN_TRANSACTION_FILE,
        usecols=get_transaction_columns(),
    )

    train_identity = pd.read_csv(
        TRAIN_IDENTITY_FILE,
        usecols=get_identity_columns(),
    )

    return train_transaction, train_identity


def merge_identity_data(
    train_transaction: pd.DataFrame,
    train_identity: pd.DataFrame,
) -> pd.DataFrame:
    identity_df = train_identity.copy()
    identity_df["has_identity"] = 1

    merged_df = train_transaction.merge(
        identity_df,
        on="TransactionID",
        how="left",
    )

    merged_df["has_identity"] = merged_df["has_identity"].fillna(0).astype(int)

    return merged_df


def add_engineered_features(df: pd.DataFrame) -> pd.DataFrame:
    feature_df = df.copy()

    feature_df["TransactionAmt_log"] = np.log1p(feature_df["TransactionAmt"])
    feature_df["transaction_hour"] = (feature_df["TransactionDT"] // 3600) % 24
    feature_df["transaction_day"] = feature_df["TransactionDT"] // 86400

    feature_df["P_emaildomain_missing"] = feature_df["P_emaildomain"].isna().astype(int)
    feature_df["R_emaildomain_missing"] = feature_df["R_emaildomain"].isna().astype(int)

    feature_df["email_domain_match"] = np.where(
        feature_df["P_emaildomain"].notna() & feature_df["R_emaildomain"].notna(),
        (feature_df["P_emaildomain"] == feature_df["R_emaildomain"]).astype(int),
        -1,
    )

    card_columns = ["card1", "card2", "card3", "card4", "card5", "card6"]
    address_columns = ["addr1", "addr2"]

    feature_df["card_missing_count"] = feature_df[card_columns].isna().sum(axis=1)
    feature_df["address_missing_count"] = feature_df[address_columns].isna().sum(axis=1)

    return feature_df


def identify_high_missing_columns(df: pd.DataFrame) -> list[str]:
    missing_percentages = df.isna().mean() * 100

    high_missing_columns = missing_percentages[
        missing_percentages >= HIGH_MISSING_THRESHOLD
    ].index.tolist()

    return high_missing_columns


def identify_near_constant_columns(df: pd.DataFrame) -> list[str]:
    near_constant_columns = []

    for column in df.columns:
        top_frequency = df[column].value_counts(dropna=False, normalize=True).head(1)

        if not top_frequency.empty and top_frequency.iloc[0] >= NEAR_CONSTANT_THRESHOLD:
            near_constant_columns.append(column)

    return near_constant_columns


def group_rare_categories(series: pd.Series) -> pd.Series:
    counts = series.value_counts(dropna=False)

    return series.where(
        series.map(counts) >= RARE_CATEGORY_MIN_COUNT,
        "rare",
    )


def clean_features(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series, dict]:
    target = df["isFraud"].copy()

    features = df.drop(
        columns=[
            "TransactionID",
            "isFraud",
            "TransactionDT",
        ],
        errors="ignore",
    )

    high_missing_columns = identify_high_missing_columns(features)
    features = features.drop(columns=high_missing_columns, errors="ignore")

    near_constant_columns = identify_near_constant_columns(features)
    features = features.drop(columns=near_constant_columns, errors="ignore")

    numeric_columns = features.select_dtypes(include=["number"]).columns.tolist()
    categorical_columns = features.select_dtypes(include=["object"]).columns.tolist()

    for column in numeric_columns:
        median_value = features[column].median()
        features[column] = features[column].fillna(median_value)

    for column in categorical_columns:
        features[column] = features[column].fillna("missing").astype(str)
        features[column] = group_rare_categories(features[column])

    cleaning_info = {
        "high_missing_columns": high_missing_columns,
        "near_constant_columns": near_constant_columns,
        "numeric_columns": numeric_columns,
        "categorical_columns": categorical_columns,
    }

    return features, target, cleaning_info


def create_summary(
    raw_df: pd.DataFrame,
    features: pd.DataFrame,
    target: pd.Series,
    cleaning_info: dict,
) -> pd.DataFrame:
    records = [
        {
            "metric": "raw_rows",
            "value": raw_df.shape[0],
        },
        {
            "metric": "raw_columns",
            "value": raw_df.shape[1],
        },
        {
            "metric": "processed_rows",
            "value": features.shape[0],
        },
        {
            "metric": "processed_feature_columns",
            "value": features.shape[1],
        },
        {
            "metric": "fraud_count",
            "value": int(target.sum()),
        },
        {
            "metric": "non_fraud_count",
            "value": int((target == 0).sum()),
        },
        {
            "metric": "fraud_percentage",
            "value": round(target.mean() * 100, 3),
        },
        {
            "metric": "high_missing_columns_dropped_count",
            "value": len(cleaning_info["high_missing_columns"]),
        },
        {
            "metric": "near_constant_columns_dropped_count",
            "value": len(cleaning_info["near_constant_columns"]),
        },
        {
            "metric": "numeric_feature_count",
            "value": len(features.select_dtypes(include=["number"]).columns),
        },
        {
            "metric": "categorical_feature_count",
            "value": len(features.select_dtypes(include=["object"]).columns),
        },
        {
            "metric": "output_dataset",
            "value": str(OUTPUT_DATASET_FILE),
        },
    ]

    return pd.DataFrame(records)


def save_processed_dataset(features: pd.DataFrame, target: pd.Series) -> None:
    processed_df = pd.concat(
        [
            target.rename("isFraud"),
            features,
        ],
        axis=1,
    )

    processed_df.to_csv(
        OUTPUT_DATASET_FILE,
        index=False,
        compression="gzip",
    )


def print_report(
    summary: pd.DataFrame,
    cleaning_info: dict,
    features: pd.DataFrame,
) -> None:
    print("Baseline Feature Dataset Build Report")
    print("=" * 80)
    print(summary)
    print()

    print("Dropped high-missing columns:")
    print(cleaning_info["high_missing_columns"])
    print()

    print("Dropped near-constant columns:")
    print(cleaning_info["near_constant_columns"])
    print()

    print("Final feature columns:")
    print(features.columns.tolist())
    print()


def main() -> None:
    create_output_directories()

    train_transaction, train_identity = load_selected_raw_data()
    merged_df = merge_identity_data(train_transaction, train_identity)
    engineered_df = add_engineered_features(merged_df)

    features, target, cleaning_info = clean_features(engineered_df)

    save_processed_dataset(features, target)

    summary = create_summary(engineered_df, features, target, cleaning_info)
    summary.to_csv(SUMMARY_FILE, index=False)

    print_report(summary, cleaning_info, features)

    print(f"Processed baseline dataset saved to: {OUTPUT_DATASET_FILE}")
    print(f"Summary saved to: {SUMMARY_FILE}")


if __name__ == "__main__":
    main()
