import warnings
from pathlib import Path

import joblib
import pandas as pd
from sklearn.exceptions import InconsistentVersionWarning

warnings.filterwarnings("ignore", category=InconsistentVersionWarning)
warnings.filterwarnings(
    "ignore",
    message="X does not have valid feature names.*",
    category=UserWarning,
)


def find_workspace_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()

    for path in [current, *current.parents]:
        if (path / "data" / "processed" / "baseline_modeling_dataset.csv.gz").exists():
            return path

    return current


WORKSPACE_ROOT = find_workspace_root()
DATASET_FILE = WORKSPACE_ROOT / "data" / "processed" / "baseline_modeling_dataset.csv.gz"
MODEL_FILE = WORKSPACE_ROOT / "ml" / "model_artifacts" / "lightgbm_fraud_model.joblib"
REPORTS_DIR = WORKSPACE_ROOT / "reports" / "model_reports"
SCORED_OUTPUT_FILE = REPORTS_DIR / "lightgbm_scored_sample_transactions.csv"
FRAUD_THRESHOLD = 0.84
SAMPLE_SIZE = 20


def create_output_directories() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def load_dataset() -> pd.DataFrame:
    if not DATASET_FILE.exists():
        raise FileNotFoundError(
            f"Processed dataset not found: {DATASET_FILE}. "
            "Run ml/src/features/build_baseline_feature_dataset.py first."
        )

    return pd.read_csv(DATASET_FILE)


def load_model():
    if not MODEL_FILE.exists():
        raise FileNotFoundError(
            f"LightGBM model not found: {MODEL_FILE}. "
            "Run ml/src/models/train_lightgbm_model.py first."
        )

    return joblib.load(MODEL_FILE)


def assign_risk_band(fraud_probability: float) -> str:
    if fraud_probability >= 0.84:
        return "high"
    if fraud_probability >= 0.50:
        return "medium"
    if fraud_probability >= 0.25:
        return "low"
    return "very_low"


def score_transactions(
    model,
    transactions: pd.DataFrame,
    threshold: float,
) -> pd.DataFrame:
    features = transactions.drop(columns=["isFraud"], errors="ignore")

    fraud_probabilities = model.predict_proba(features)[:, 1]
    fraud_predictions = (fraud_probabilities >= threshold).astype(int)

    scored_df = transactions.copy()
    scored_df["fraud_probability"] = fraud_probabilities
    scored_df["fraud_prediction"] = fraud_predictions
    scored_df["fraud_threshold"] = threshold
    scored_df["risk_band"] = scored_df["fraud_probability"].apply(assign_risk_band)

    return scored_df


def select_sample_transactions(df: pd.DataFrame) -> pd.DataFrame:
    fraud_cases = df[df["isFraud"] == 1].head(SAMPLE_SIZE // 2)
    non_fraud_cases = df[df["isFraud"] == 0].head(SAMPLE_SIZE // 2)

    sample_df = pd.concat([fraud_cases, non_fraud_cases], axis=0)
    sample_df = sample_df.sample(frac=1, random_state=42).reset_index(drop=True)

    return sample_df


def print_report(scored_df: pd.DataFrame) -> None:
    output_columns = [
        "isFraud",
        "fraud_probability",
        "fraud_prediction",
        "fraud_threshold",
        "risk_band",
    ]

    print("LightGBM Fraud Inference Report")
    print("=" * 80)
    print(scored_df[output_columns])
    print()

    print("Risk band distribution:")
    print(scored_df["risk_band"].value_counts())
    print()

    print("Prediction distribution:")
    print(scored_df["fraud_prediction"].value_counts())


def main() -> None:
    create_output_directories()

    df = load_dataset()
    model = load_model()

    sample_transactions = select_sample_transactions(df)

    scored_df = score_transactions(
        model=model,
        transactions=sample_transactions,
        threshold=FRAUD_THRESHOLD,
    )

    scored_df.to_csv(SCORED_OUTPUT_FILE, index=False)

    print_report(scored_df)

    print(f"Scored transactions saved to: {SCORED_OUTPUT_FILE}")


if __name__ == "__main__":
    main()
