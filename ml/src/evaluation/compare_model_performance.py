from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def find_workspace_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()

    for path in [current, *current.parents]:
        if (path / "data" / "processed" / "baseline_modeling_dataset.csv.gz").exists():
            return path

    return current


WORKSPACE_ROOT = find_workspace_root()
REPORTS_DIR = WORKSPACE_ROOT / "reports" / "model_reports"
FIGURES_DIR = WORKSPACE_ROOT / "reports" / "figures"
MODEL_METRIC_FILES = {
    "Baseline SGD Logistic": REPORTS_DIR / "baseline_model_metrics.csv",
    "XGBoost": REPORTS_DIR / "xgboost_model_metrics.csv",
    "LightGBM": REPORTS_DIR / "lightgbm_model_metrics.csv",
}
OUTPUT_COMPARISON_FILE = REPORTS_DIR / "model_comparison.csv"


def create_output_directories() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)


def load_model_metrics() -> pd.DataFrame:
    records = []
    for model_name, metrics_file in MODEL_METRIC_FILES.items():
        if not metrics_file.exists():
            raise FileNotFoundError(
                f"Missing metrics file: {metrics_file}. "
                f"Run the training script for {model_name} first."
            )

        metrics_df = pd.read_csv(metrics_file)
        record = {"model": model_name}
        for _, row in metrics_df.iterrows():
            record[row["metric"]] = row["value"]
        records.append(record)

    comparison_df = pd.DataFrame(records)
    metric_order = [
        "model",
        "accuracy",
        "precision",
        "recall",
        "f1_score",
        "roc_auc",
        "average_precision_pr_auc",
    ]
    return comparison_df[metric_order]


def identify_best_models(comparison_df: pd.DataFrame) -> pd.DataFrame:
    metric_columns = [
        "accuracy",
        "precision",
        "recall",
        "f1_score",
        "roc_auc",
        "average_precision_pr_auc",
    ]
    records = []
    for metric in metric_columns:
        best_row = comparison_df.loc[comparison_df[metric].idxmax()]
        records.append(
            {
                "metric": metric,
                "best_model": best_row["model"],
                "best_value": best_row[metric],
            }
        )
    return pd.DataFrame(records)


def plot_model_metric_comparison(comparison_df: pd.DataFrame) -> None:
    plot_df = comparison_df.set_index("model")[
        [
            "accuracy",
            "precision",
            "recall",
            "f1_score",
            "roc_auc",
            "average_precision_pr_auc",
        ]
    ]
    plt.figure(figsize=(12, 6))
    plot_df.plot(kind="bar")
    plt.title("Model Metric Comparison")
    plt.xlabel("Model")
    plt.ylabel("Metric Value")
    plt.xticks(rotation=20, ha="right")
    plt.legend(loc="lower right")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "model_metric_comparison.png")
    plt.close()


def plot_pr_auc_comparison(comparison_df: pd.DataFrame) -> None:
    plot_df = comparison_df.sort_values("average_precision_pr_auc")
    plt.figure(figsize=(8, 5))
    plt.barh(plot_df["model"], plot_df["average_precision_pr_auc"])
    plt.title("Model PR-AUC Comparison")
    plt.xlabel("Average Precision / PR-AUC")
    plt.ylabel("Model")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "model_pr_auc_comparison.png")
    plt.close()


def plot_precision_recall_comparison(comparison_df: pd.DataFrame) -> None:
    plot_df = comparison_df.set_index("model")[["precision", "recall"]]
    plt.figure(figsize=(8, 5))
    plot_df.plot(kind="bar")
    plt.title("Precision and Recall Comparison")
    plt.xlabel("Model")
    plt.ylabel("Metric Value")
    plt.xticks(rotation=20, ha="right")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "model_precision_recall_comparison.png")
    plt.close()


def print_report(comparison_df: pd.DataFrame, best_models_df: pd.DataFrame) -> None:
    print("Model Performance Comparison")
    print("=" * 80)
    print(comparison_df)
    print()
    print("Best model by metric:")
    print(best_models_df)
    print()
    best_pr_auc_model = best_models_df[
        best_models_df["metric"] == "average_precision_pr_auc"
    ]["best_model"].iloc[0]
    print(f"Best model by PR-AUC: {best_pr_auc_model}")


def main() -> None:
    create_output_directories()
    comparison_df = load_model_metrics()
    best_models_df = identify_best_models(comparison_df)
    comparison_df.to_csv(OUTPUT_COMPARISON_FILE, index=False)
    plot_model_metric_comparison(comparison_df)
    plot_pr_auc_comparison(comparison_df)
    plot_precision_recall_comparison(comparison_df)
    print_report(comparison_df, best_models_df)
    print(f"Model comparison saved to: {OUTPUT_COMPARISON_FILE}")
    print(f"Figures saved to: {FIGURES_DIR}")


if __name__ == "__main__":
    main()
