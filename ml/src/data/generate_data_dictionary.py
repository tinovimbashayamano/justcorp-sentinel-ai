from pathlib import Path
import pandas as pd


DATA_DIR = Path("data/raw")
OUTPUT_DIR = Path("docs/data")
OUTPUT_FILE = OUTPUT_DIR / "data_dictionary_generated.csv"

FILES = {
    "train_transaction": "train_transaction.csv",
    "train_identity": "train_identity.csv",
}


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
    if column_name.startswith("card"):
        return "card_feature"
    if column_name.startswith("addr"):
        return "address_feature"
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


def inspect_dataset(file_label: str, file_name: str) -> pd.DataFrame:
    file_path = DATA_DIR / file_name

    if not file_path.exists():
        raise FileNotFoundError(f"Missing file: {file_path}")

    df = pd.read_csv(file_path, nrows=10000)

    total_rows = sum(1 for _ in open(file_path, encoding="utf-8")) - 1

    records = []

    for column in df.columns:
        missing_count_sample = df[column].isna().sum()
        missing_percentage_sample = (missing_count_sample / len(df)) * 100

        records.append(
            {
                "dataset": file_label,
                "column_name": column,
                "column_group": classify_column(column),
                "data_type_sample": str(df[column].dtype),
                "missing_percentage_sample": round(missing_percentage_sample, 2),
                "sample_values": df[column].dropna().astype(str).head(3).tolist(),
                "total_rows_in_file": total_rows,
            }
        )

    return pd.DataFrame(records)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    dictionaries = []

    for file_label, file_name in FILES.items():
        print(f"Inspecting {file_name}...")
        dictionaries.append(inspect_dataset(file_label, file_name))

    final_dictionary = pd.concat(dictionaries, ignore_index=True)
    final_dictionary.to_csv(OUTPUT_FILE, index=False)

    print(f"Data dictionary generated: {OUTPUT_FILE}")
    print(f"Total columns documented: {len(final_dictionary)}")
    print()
    print("Column group counts:")
    print(final_dictionary["column_group"].value_counts())


if __name__ == "__main__":
    main()
