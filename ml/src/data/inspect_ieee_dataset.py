from pathlib import Path
import pandas as pd


DATA_DIR = Path("data/raw")

files = [
    "train_transaction.csv",
    "train_identity.csv",
    "test_transaction.csv",
    "test_identity.csv",
    "sample_submission.csv",
]


def inspect_file(file_name: str) -> None:
    file_path = DATA_DIR / file_name

    if not file_path.exists():
        print(f"{file_name}: NOT FOUND")
        return

    df_preview = pd.read_csv(file_path, nrows=5)

    row_count = sum(1 for _ in open(file_path, encoding="utf-8")) - 1
    column_count = len(df_preview.columns)

    print("=" * 80)
    print(f"File: {file_name}")
    print(f"Rows: {row_count}")
    print(f"Columns: {column_count}")
    print("First 10 columns:")
    print(list(df_preview.columns[:10]))

    if "isFraud" in df_preview.columns:
        full_target = pd.read_csv(file_path, usecols=["isFraud"])
        print("Target distribution:")
        print(full_target["isFraud"].value_counts())
        print("Target percentage:")
        print(full_target["isFraud"].value_counts(normalize=True) * 100)


def main() -> None:
    print("IEEE-CIS Dataset Inspection")
    print(f"Dataset folder: {DATA_DIR}")

    for file_name in files:
        inspect_file(file_name)


if __name__ == "__main__":
    main()
