from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    classification_report,
    confusion_matrix,
    ConfusionMatrixDisplay,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


def find_workspace_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()

    for path in [current, *current.parents]:
        if (path / "data" / "processed" / "baseline_modeling_dataset.csv.gz").exists():
            return path

    return current


WORKSPACE_ROOT = find_workspace_root()
DATASET_FILE = WORKSPACE_ROOT / "data" / "processed" / "baseline_modeling_dataset.csv.gz"
FIGURES_DIR = WORKSPACE_ROOT / "reports" / "figures"
REPORTS_DIR = WORKSPACE_ROOT / "reports" / "model_reports"
MODEL_DIR = WORKSPACE_ROOT / "ml" / "model_artifacts"
DOCS_DIR = WORKSPACE_ROOT / "docs" / "modeling"
METRICS_FILE = REPORTS_DIR / "lightgbm_model_metrics.csv"
CLASSIFICATION_REPORT_FILE = REPORTS_DIR / "lightgbm_classification_report.txt"
MODEL_FILE = MODEL_DIR / "lightgbm_fraud_model.joblib"
RANDOM_STATE = 42
TEST_SIZE = 0.2


def create_output_directories() -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)


def load_dataset() -> tuple[pd.DataFrame, pd.Series]:
    if not DATASET_FILE.exists():
        raise FileNotFoundError(
            f"Processed dataset not found: {DATASET_FILE}. "
            "Run the baseline feature dataset build script first."
        )

    df = pd.read_csv(DATASET_FILE)
    target = df["isFraud"]
    features = df.drop(columns=["isFraud"])
    return features, target


def build_preprocessing_pipeline(features: pd.DataFrame) -> ColumnTransformer:
    numeric_columns = features.select_dtypes(include=["number"]).columns.tolist()
    categorical_columns = features.select_dtypes(include=["object"]).columns.tolist()

    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
        ]
    )

    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="constant", fill_value="missing")),
            (
                "encoder",
                OneHotEncoder(
                    handle_unknown="ignore",
                    sparse_output=True,
                ),
            ),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("numeric", numeric_pipeline, numeric_columns),
            ("categorical", categorical_pipeline, categorical_columns),
        ]
    )
    return preprocessor


def calculate_scale_pos_weight(y_train: pd.Series) -> float:
    negative_count = (y_train == 0).sum()
    positive_count = (y_train == 1).sum()
    return negative_count / positive_count


def build_model_pipeline(features: pd.DataFrame, scale_pos_weight: float) -> Pipeline:
    preprocessor = build_preprocessing_pipeline(features)
    classifier = LGBMClassifier(
        n_estimators=300,
        learning_rate=0.05,
        num_leaves=31,
        max_depth=-1,
        subsample=0.8,
        colsample_bytree=0.8,
        objective="binary",
        scale_pos_weight=scale_pos_weight,
        random_state=RANDOM_STATE,
        n_jobs=-1,
        verbose=-1,
    )

    model_pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", classifier),
        ]
    )
    return model_pipeline


def calculate_metrics(
    y_test: pd.Series,
    y_pred: pd.Series,
    y_proba: pd.Series,
) -> pd.DataFrame:
    metrics = [
        {
            "metric": "accuracy",
            "value": accuracy_score(y_test, y_pred),
        },
        {
            "metric": "precision",
            "value": precision_score(y_test, y_pred, zero_division=0),
        },
        {
            "metric": "recall",
            "value": recall_score(y_test, y_pred, zero_division=0),
        },
        {
            "metric": "f1_score",
            "value": f1_score(y_test, y_pred, zero_division=0),
        },
        {
            "metric": "roc_auc",
            "value": roc_auc_score(y_test, y_proba),
        },
        {
            "metric": "average_precision_pr_auc",
            "value": average_precision_score(y_test, y_proba),
        },
    ]
    return pd.DataFrame(metrics)


def save_classification_report(y_test: pd.Series, y_pred: pd.Series) -> None:
    report = classification_report(
        y_test,
        y_pred,
        target_names=["non_fraud", "fraud"],
        zero_division=0,
    )
    CLASSIFICATION_REPORT_FILE.write_text(report, encoding="utf-8")


def plot_confusion_matrix(y_test: pd.Series, y_pred: pd.Series) -> None:
    matrix = confusion_matrix(y_test, y_pred)
    display = ConfusionMatrixDisplay(
        confusion_matrix=matrix,
        display_labels=["non_fraud", "fraud"],
    )
    display.plot(values_format="d")
    plt.title("LightGBM Model Confusion Matrix")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "lightgbm_confusion_matrix.png")
    plt.close()


def plot_precision_recall_curve(y_test: pd.Series, y_proba: pd.Series) -> None:
    precision, recall, _ = precision_recall_curve(y_test, y_proba)
    plt.figure(figsize=(7, 5))
    plt.plot(recall, precision)
    plt.title("LightGBM Precision-Recall Curve")
    plt.xlabel("Recall")
    plt.ylabel("Precision")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "lightgbm_precision_recall_curve.png")
    plt.close()


def get_feature_names(model_pipeline: Pipeline) -> list[str]:
    preprocessor = model_pipeline.named_steps["preprocessor"]
    try:
        feature_names = preprocessor.get_feature_names_out()
        return [str(feature) for feature in feature_names]
    except Exception:
        return [
            f"feature_{index}"
            for index in range(len(model_pipeline.named_steps["classifier"].feature_importances_))
        ]


def plot_feature_importance(model_pipeline: Pipeline) -> None:
    classifier = model_pipeline.named_steps["classifier"]
    feature_names = get_feature_names(model_pipeline)
    importance_df = pd.DataFrame(
        {
            "feature": feature_names,
            "importance": classifier.feature_importances_,
        }
    ).sort_values("importance", ascending=False)
    top_features = importance_df.head(20).sort_values("importance")
    plt.figure(figsize=(10, 7))
    plt.barh(top_features["feature"], top_features["importance"])
    plt.title("Top LightGBM Feature Importances")
    plt.xlabel("Importance")
    plt.ylabel("Feature")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "lightgbm_feature_importance.png")
    plt.close()


def print_report(
    metrics_df: pd.DataFrame,
    y_test: pd.Series,
    y_pred: pd.Series,
    scale_pos_weight: float,
) -> None:
    print("LightGBM Fraud Detection Model Report")
    print("=" * 80)
    print(f"scale_pos_weight: {scale_pos_weight:.3f}")
    print()
    print(metrics_df)
    print()
    print("Confusion matrix:")
    print(confusion_matrix(y_test, y_pred))
    print()
    print("Classification report:")
    print(
        classification_report(
            y_test,
            y_pred,
            target_names=["non_fraud", "fraud"],
            zero_division=0,
        )
    )


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

    scale_pos_weight = calculate_scale_pos_weight(y_train)
    model_pipeline = build_model_pipeline(features, scale_pos_weight)

    print("Training LightGBM model. This may take several minutes...")
    model_pipeline.fit(X_train, y_train)

    y_pred = model_pipeline.predict(X_test)
    y_proba = model_pipeline.predict_proba(X_test)[:, 1]

    metrics_df = calculate_metrics(y_test, y_pred, y_proba)
    metrics_df.to_csv(METRICS_FILE, index=False)

    save_classification_report(y_test, y_pred)
    plot_confusion_matrix(y_test, y_pred)
    plot_precision_recall_curve(y_test, y_proba)
    plot_feature_importance(model_pipeline)

    joblib.dump(model_pipeline, MODEL_FILE)

    print_report(metrics_df, y_test, y_pred, scale_pos_weight)
    print(f"Metrics saved to: {METRICS_FILE}")
    print(f"Classification report saved to: {CLASSIFICATION_REPORT_FILE}")
    print(f"Model saved to: {MODEL_FILE}")
    print(f"Figures saved to: {FIGURES_DIR}")


if __name__ == "__main__":
    main()
