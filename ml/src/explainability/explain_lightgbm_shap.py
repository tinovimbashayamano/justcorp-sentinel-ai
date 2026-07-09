from pathlib import Path

import joblib
import matplotlib
import numpy as np
import pandas as pd
import shap
from sklearn.model_selection import train_test_split

matplotlib.use("Agg")

import matplotlib.pyplot as plt


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
FIGURES_DIR = WORKSPACE_ROOT / "reports" / "figures"
SHAP_IMPORTANCE_FILE = REPORTS_DIR / "lightgbm_shap_feature_importance.csv"
LOCAL_EXPLANATIONS_FILE = REPORTS_DIR / "lightgbm_local_explanations.csv"
RANDOM_STATE = 42
TEST_SIZE = 0.2
SHAP_SAMPLE_SIZE = 2000
LOCAL_CASE_COUNT = 5
TOP_LOCAL_FEATURES = 10


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


def get_feature_names(model_pipeline) -> list[str]:
    preprocessor = model_pipeline.named_steps["preprocessor"]
    try:
        feature_names = preprocessor.get_feature_names_out()
        return [str(feature) for feature in feature_names]
    except Exception:
        classifier = model_pipeline.named_steps["classifier"]
        return [f"feature_{index}" for index in range(len(classifier.feature_importances_))]


def transform_features(model_pipeline, features: pd.DataFrame):
    preprocessor = model_pipeline.named_steps["preprocessor"]
    transformed_features = preprocessor.transform(features)
    if hasattr(transformed_features, "toarray"):
        transformed_features = transformed_features.toarray()
    return transformed_features


def extract_positive_class_shap_values(shap_values):
    if isinstance(shap_values, list):
        return shap_values[1]
    if isinstance(shap_values, np.ndarray) and shap_values.ndim == 3:
        return shap_values[:, :, 1]
    return shap_values


def calculate_shap_values(model_pipeline, transformed_features):
    classifier = model_pipeline.named_steps["classifier"]
    explainer = shap.TreeExplainer(classifier)
    shap_values = explainer.shap_values(transformed_features)
    positive_class_shap_values = extract_positive_class_shap_values(shap_values)
    return positive_class_shap_values


def create_shap_importance(
    shap_values,
    feature_names: list[str],
) -> pd.DataFrame:
    importance_df = pd.DataFrame(
        {
            "feature": feature_names,
            "mean_absolute_shap_value": np.abs(shap_values).mean(axis=0),
        }
    ).sort_values("mean_absolute_shap_value", ascending=False)
    return importance_df


def plot_shap_summary_bar(
    shap_values,
    transformed_features,
    feature_names: list[str],
) -> None:
    shap.summary_plot(
        shap_values,
        transformed_features,
        feature_names=feature_names,
        plot_type="bar",
        max_display=20,
        show=False,
    )
    plt.title("LightGBM SHAP Global Feature Importance")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "lightgbm_shap_summary_bar.png", bbox_inches="tight")
    plt.close()


def plot_shap_beeswarm(
    shap_values,
    transformed_features,
    feature_names: list[str],
) -> None:
    shap.summary_plot(
        shap_values,
        transformed_features,
        feature_names=feature_names,
        max_display=20,
        show=False,
    )
    plt.title("LightGBM SHAP Beeswarm Plot")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "lightgbm_shap_beeswarm.png", bbox_inches="tight")
    plt.close()


def create_local_explanations(
    model_pipeline,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    feature_names: list[str],
) -> pd.DataFrame:
    y_proba = model_pipeline.predict_proba(X_test)[:, 1]
    high_risk_positions = np.argsort(y_proba)[-LOCAL_CASE_COUNT:][::-1]
    X_cases = X_test.iloc[high_risk_positions]
    y_cases = y_test.iloc[high_risk_positions]
    y_proba_cases = y_proba[high_risk_positions]
    transformed_cases = transform_features(model_pipeline, X_cases)
    shap_values_cases = calculate_shap_values(model_pipeline, transformed_cases)

    records = []
    for case_number, position in enumerate(range(len(X_cases)), start=1):
        case_shap_values = shap_values_cases[position]
        top_feature_indices = np.argsort(np.abs(case_shap_values))[-TOP_LOCAL_FEATURES:][::-1]
        for rank, feature_index in enumerate(top_feature_indices, start=1):
            records.append(
                {
                    "case_number": case_number,
                    "true_label": int(y_cases.iloc[position]),
                    "predicted_fraud_probability": float(y_proba_cases[position]),
                    "rank": rank,
                    "feature": feature_names[feature_index],
                    "shap_value": float(case_shap_values[feature_index]),
                    "impact_direction": (
                        "increases_fraud_risk"
                        if case_shap_values[feature_index] > 0
                        else "decreases_fraud_risk"
                    ),
                }
            )
    return pd.DataFrame(records)


def print_report(
    importance_df: pd.DataFrame,
    local_explanations_df: pd.DataFrame,
    sample_size: int,
) -> None:
    print("LightGBM SHAP Explainability Report")
    print("=" * 80)
    print(f"SHAP sample size: {sample_size}")
    print()
    print("Top 20 global SHAP features:")
    print(importance_df.head(20))
    print()
    print("Local explanations for high-risk cases:")
    print(local_explanations_df.head(30))
    print()


def main() -> None:
    create_output_directories()
    features, target = load_dataset()
    model_pipeline = load_model()
    _, X_test, _, y_test = train_test_split(
        features,
        target,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=target,
    )
    sample_size = min(SHAP_SAMPLE_SIZE, len(X_test))
    X_sample = X_test.sample(n=sample_size, random_state=RANDOM_STATE)
    transformed_sample = transform_features(model_pipeline, X_sample)
    feature_names = get_feature_names(model_pipeline)
    shap_values = calculate_shap_values(model_pipeline, transformed_sample)
    importance_df = create_shap_importance(shap_values, feature_names)
    importance_df.to_csv(SHAP_IMPORTANCE_FILE, index=False)
    local_explanations_df = create_local_explanations(
        model_pipeline,
        X_test,
        y_test,
        feature_names,
    )
    local_explanations_df.to_csv(LOCAL_EXPLANATIONS_FILE, index=False)
    plot_shap_summary_bar(shap_values, transformed_sample, feature_names)
    plot_shap_beeswarm(shap_values, transformed_sample, feature_names)
    print_report(importance_df, local_explanations_df, sample_size)
    print(f"SHAP feature importance saved to: {SHAP_IMPORTANCE_FILE}")
    print(f"Local explanations saved to: {LOCAL_EXPLANATIONS_FILE}")
    print(f"Figures saved to: {FIGURES_DIR}")


if __name__ == "__main__":
    main()
