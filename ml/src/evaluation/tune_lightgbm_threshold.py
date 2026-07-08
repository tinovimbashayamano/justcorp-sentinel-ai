import warnings
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.exceptions import InconsistentVersionWarning
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    ConfusionMatrixDisplay,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split

warnings.filterwarnings("ignore", category=InconsistentVersionWarning)
warnings.filterwarnings(
    "ignore",
    message="X does not have valid feature names.*",
    category=UserWarning,
)

DATASET_FILE = Path("data/processed/baseline_modeling_dataset.csv.gz")
MODEL_FILE = Path("ml/model_artifacts/lightgbm_fraud_model.joblib")
REPORTS_DIR = Path("reports/model_reports")
FIGURES_DIR = Path("reports/figures")
THRESHOLD_RESULTS_FILE = REPORTS_DIR / "lightgbm_threshold_tuning.csv"
RANDOM_STATE = 42
TEST_SIZE = 0.2


def create_output_directories() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)


def load_dataset() -> tuple[pd.DataFrame, pd.Series]:
    if not DATASET_FILE.exists():
        raise FileNotFoundError(
            f"Processed dataset not found: {DATASET_FILE}. "
            "Run ml/src/features/build_baseline_feature_dataset.py first."
        )

    df = pd.read_csv(DATASET_FILE)
    target = df["isFraud"]
    features = df.drop(columns=["isFraud"])
    return features, target


def load_model():
    if not MODEL_FILE.exists():
        raise FileNotFoundError(
            f"LightGBM model not found: {MODEL_FILE}. "
            "Run ml/src/models/train_lightgbm_model.py first."
        )
    return joblib.load(MODEL_FILE)


def evaluate_thresholds(y_true: pd.Series, y_proba: np.ndarray) -> pd.DataFrame:
    thresholds = np.arange(0.05, 0.96, 0.01)
    records = []
    for threshold in thresholds:
        y_pred = (y_proba >= threshold).astype(int)
        records.append(
            {
                "threshold": round(float(threshold), 2),
                "accuracy": accuracy_score(y_true, y_pred),
                "precision": precision_score(y_true, y_pred, zero_division=0),
                "recall": recall_score(y_true, y_pred, zero_division=0),
                "f1_score": f1_score(y_true, y_pred, zero_division=0),
                "predicted_fraud_count": int(y_pred.sum()),
            }
        )
    return pd.DataFrame(records)


def select_best_threshold(threshold_df: pd.DataFrame) -> pd.Series:
    return threshold_df.loc[threshold_df["f1_score"].idxmax()]


def plot_threshold_metrics(threshold_df: pd.DataFrame) -> None:
    plt.figure(figsize=(9, 5))
    plt.plot(threshold_df["threshold"], threshold_df["precision"], label="Precision")
    plt.plot(threshold_df["threshold"], threshold_df["recall"], label="Recall")
    plt.plot(threshold_df["threshold"], threshold_df["f1_score"], label="F1-score")
    plt.title("LightGBM Threshold Tuning")
    plt.xlabel("Classification Threshold")
    plt.ylabel("Metric Value")
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "lightgbm_threshold_metrics.png")
    plt.close()


def plot_best_threshold_confusion_matrix(
    y_true: pd.Series,
    y_proba: np.ndarray,
    best_threshold: float,
) -> None:
    y_pred = (y_proba >= best_threshold).astype(int)
    matrix = confusion_matrix(y_true, y_pred)
    display = ConfusionMatrixDisplay(
        confusion_matrix=matrix,
        display_labels=["non_fraud", "fraud"],
    )
    display.plot(values_format="d")
    plt.title(f"LightGBM Confusion Matrix at Threshold {best_threshold:.2f}")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "lightgbm_best_threshold_confusion_matrix.png")
    plt.close()


def print_report(threshold_df: pd.DataFrame, best_threshold_row: pd.Series) -> None:
    print("LightGBM Threshold Tuning Report")
    print("=" * 80)
    print("Best threshold by F1-score:")
    print(best_threshold_row)
    print()
    print("Top 10 thresholds by F1-score:")
    print(threshold_df.sort_values("f1_score", ascending=False).head(10))
    print()
    print("Default threshold 0.50 metrics:")
    default_row = threshold_df[threshold_df["threshold"] == 0.50]
    print(default_row)


def main() -> None:
    create_output_directories()
    features, target = load_dataset()
    X_train, X_test, y_train, y_test = train_test_split(
        features,
        target,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=target,
    )
    model = load_model()
    X_test = X_test.copy()
    y_proba = model.predict_proba(X_test)[:, 1]
    threshold_df = evaluate_thresholds(y_test, y_proba)
    threshold_df.to_csv(THRESHOLD_RESULTS_FILE, index=False)
    best_threshold_row = select_best_threshold(threshold_df)
    best_threshold = float(best_threshold_row["threshold"])
    plot_threshold_metrics(threshold_df)
    plot_best_threshold_confusion_matrix(y_test, y_proba, best_threshold)
    print_report(threshold_df, best_threshold_row)
    print(f"Threshold tuning results saved to: {THRESHOLD_RESULTS_FILE}")
    print(f"Figures saved to: {FIGURES_DIR}")


if __name__ == "__main__":
    main()
