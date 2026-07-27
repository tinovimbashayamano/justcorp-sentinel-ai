"""Plotting and report exports for local and global SHAP explanations."""

from __future__ import annotations

import base64
import html
import io
from datetime import UTC, datetime
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402

from backend.app.services.explainability_service import (
    explainability_service,
)
from backend.app.services.model_insight_service import (
    ModelInsightError,
    ModelInsightNotFoundError,
    model_insight_service,
)


class VisualizationServiceError(RuntimeError):
    """Raised when visualization data or an export cannot be produced."""


class ExplainabilityVisualizationService:
    """Build plot-ready SHAP data, PNG plots, and investigation reports."""

    def __init__(
        self,
        local_service: Any = explainability_service,
        global_service: Any = model_insight_service,
    ) -> None:
        self.local_service = local_service
        self.global_service = global_service

    @staticmethod
    def _map(value: Any) -> dict[str, Any]:
        if isinstance(value, dict):
            return value
        if hasattr(value, "model_dump"):
            return value.model_dump()
        if hasattr(value, "dict"):
            return value.dict()
        raise VisualizationServiceError(
            f"Unsupported response type: {type(value).__name__}"
        )

    def _local(
        self,
        features: dict[str, Any],
        top_features: int,
    ) -> dict[str, Any]:
        method = getattr(self.local_service, "explain", None) or getattr(
            self.local_service,
            "explain_transaction",
            None,
        )
        if method is None:
            raise VisualizationServiceError(
                "Local explainability method not found."
            )

        try:
            try:
                result = method(
                    features,
                    top_features=top_features,
                )
            except TypeError:
                result = method(features, top_n=top_features)
        except (TypeError, ValueError):
            raise
        except Exception as error:
            raise VisualizationServiceError(
                "Unable to produce a local explanation."
            ) from error

        return self._map(result)

    @staticmethod
    def _point(item: Any) -> dict[str, Any]:
        data = ExplainabilityVisualizationService._map(item)
        shap_value = float(
            data.get(
                "shap_value",
                data.get("contribution", 0.0),
            )
        )
        if shap_value > 0:
            direction = "increases_fraud_risk"
        elif shap_value < 0:
            direction = "reduces_fraud_risk"
        else:
            direction = "neutral"

        return {
            "feature": str(
                data.get("feature")
                or data.get("display_name")
                or data.get("source_feature")
                or "unknown"
            ),
            "feature_value": data.get(
                "feature_value",
                data.get("value"),
            ),
            "shap_value": shap_value,
            "absolute_impact": abs(shap_value),
            "direction": direction,
        }

    def local_visualization_data(
        self,
        transaction_id: str,
        features: dict[str, Any],
        top_features: int = 10,
    ) -> dict[str, Any]:
        explanation = self._local(features, top_features)
        contributions = (
            explanation.get("contributions")
            or explanation.get("top_features")
            or explanation.get("feature_contributions")
            or []
        )
        points = sorted(
            (self._point(item) for item in contributions),
            key=lambda item: item["absolute_impact"],
            reverse=True,
        )[:top_features]
        probability = float(
            explanation.get(
                "fraud_probability",
                explanation.get("probability", 0.0),
            )
        )
        prediction = int(
            explanation.get(
                "prediction",
                explanation.get(
                    "fraud_prediction",
                    probability >= 0.5,
                ),
            )
        )

        return {
            "transaction_id": transaction_id,
            "prediction": prediction,
            "fraud_probability": probability,
            "risk_band": str(
                explanation.get("risk_band", "unknown")
            ),
            "base_value": float(
                explanation.get("base_value", 0.0)
            ),
            "summary": str(explanation.get("summary", "")),
            "points": points,
        }

    @staticmethod
    def _png(figure: Any) -> str:
        buffer = io.BytesIO()
        try:
            figure.savefig(
                buffer,
                format="png",
                dpi=150,
                bbox_inches="tight",
            )
            buffer.seek(0)
            return base64.b64encode(buffer.read()).decode("ascii")
        finally:
            plt.close(figure)
            buffer.close()

    def waterfall_plot(
        self,
        transaction_id: str,
        features: dict[str, Any],
        top_features: int = 10,
    ) -> dict[str, Any]:
        data = self.local_visualization_data(
            transaction_id,
            features,
            top_features,
        )
        points = list(reversed(data["points"]))
        figure, axis = plt.subplots(
            figsize=(10, max(4.5, len(points) * 0.45))
        )
        axis.barh(
            [point["feature"] for point in points],
            [point["shap_value"] for point in points],
        )
        axis.axvline(0, linewidth=1)
        axis.set_xlabel("SHAP contribution")
        axis.set_title(
            f"Transaction {transaction_id}: "
            "local fraud-risk contributions"
        )
        axis.grid(axis="x", alpha=0.25)
        figure.tight_layout()

        return {
            "transaction_id": transaction_id,
            "plot_type": "waterfall",
            "media_type": "image/png",
            "image_base64": self._png(figure),
        }

    def force_plot(
        self,
        transaction_id: str,
        features: dict[str, Any],
        top_features: int = 10,
    ) -> dict[str, Any]:
        data = self.local_visualization_data(
            transaction_id,
            features,
            top_features,
        )
        total = data["base_value"]
        positions = [total]
        for point in data["points"]:
            total += point["shap_value"]
            positions.append(total)

        figure, axis = plt.subplots(figsize=(12, 4.8))
        axis.plot(
            range(len(positions)),
            positions,
            marker="o",
        )
        axis.axhline(
            data["base_value"],
            linestyle="--",
            linewidth=1,
        )
        axis.set_xticks(range(1, len(data["points"]) + 1))
        axis.set_xticklabels(
            [point["feature"] for point in data["points"]],
            rotation=35,
            ha="right",
        )
        axis.set_ylabel("Cumulative model output")
        axis.set_title(
            f"Transaction {transaction_id}: "
            "cumulative explanation path"
        )
        axis.grid(alpha=0.25)
        figure.tight_layout()

        return {
            "transaction_id": transaction_id,
            "plot_type": "force",
            "media_type": "image/png",
            "image_base64": self._png(figure),
        }

    def _global(self) -> dict[str, Any]:
        for name in (
            "compute_global_importance",
            "global_importance",
            "get_global_importance",
        ):
            method = getattr(self.global_service, name, None)
            if method is not None:
                try:
                    return self._map(method())
                except Exception as error:
                    raise VisualizationServiceError(
                        "Unable to produce global feature importance."
                    ) from error

        raise VisualizationServiceError(
            "Global importance method not found."
        )

    def global_visualization_data(
        self,
        limit: int = 20,
    ) -> dict[str, Any]:
        raw = self._global()
        items = raw.get("features") or raw.get("rankings") or []
        features = []
        for index, item in enumerate(items, start=1):
            data = self._map(item)
            features.append(
                {
                    "rank": index,
                    "feature": str(
                        data.get("feature")
                        or data.get("name")
                        or "unknown"
                    ),
                    "importance": float(
                        data.get(
                            "importance",
                            data.get(
                                "mean_abs_shap",
                                data.get("value", 0.0),
                            ),
                        )
                    ),
                }
            )

        features.sort(
            key=lambda item: item["importance"],
            reverse=True,
        )
        for index, item in enumerate(features, start=1):
            item["rank"] = index

        generated_at = raw.get("generated_at")
        if isinstance(generated_at, datetime):
            generated_at = generated_at.isoformat()
        else:
            generated_at = str(
                generated_at or datetime.now(UTC).isoformat()
            )

        return {
            "plot_type": "summary_bar",
            "samples": int(
                raw.get(
                    "samples",
                    raw.get("samples_used", 0),
                )
            ),
            "generated_at": generated_at,
            "features": features[:limit],
        }

    def global_summary_plot(
        self,
        limit: int = 20,
    ) -> dict[str, Any]:
        data = self.global_visualization_data(limit)
        points = list(reversed(data["features"]))
        figure, axis = plt.subplots(
            figsize=(10, max(5, len(points) * 0.42))
        )
        axis.barh(
            [point["feature"] for point in points],
            [point["importance"] for point in points],
        )
        axis.set_xlabel("Mean absolute SHAP value")
        axis.set_title("Global fraud-model feature importance")
        axis.grid(axis="x", alpha=0.25)
        figure.tight_layout()

        return {
            "plot_type": "summary_bar",
            "media_type": "image/png",
            "image_base64": self._png(figure),
        }

    def dependence_data(
        self,
        feature_name: str,
        limit: int = 500,
    ) -> dict[str, Any]:
        method = getattr(
            self.global_service,
            "get_dependence_data",
            None,
        )
        if method is None:
            raise VisualizationServiceError(
                "Global dependence data method not found."
            )

        try:
            raw = self._map(method(feature_name, limit=limit))
        except (KeyError, ModelInsightNotFoundError) as error:
            raise KeyError(feature_name) from error
        except ModelInsightError as error:
            raise VisualizationServiceError(
                "Unable to produce feature dependence data."
            ) from error
        except Exception as error:
            raise VisualizationServiceError(
                "Unable to produce feature dependence data."
            ) from error

        points = raw.get("points", [])[:limit]
        return {
            "feature": feature_name,
            "points": points,
            "sample_count": min(
                int(raw.get("sample_count", len(points))),
                limit,
            ),
        }

    @staticmethod
    def _safe(value: Any) -> str:
        return html.escape("" if value is None else str(value))

    def build_html_report(
        self,
        transaction_id: str,
        features: dict[str, Any],
        top_features: int = 10,
        case_id: int | None = None,
        analyst_notes: str | None = None,
        include_global_context: bool = True,
    ) -> bytes:
        local = self.local_visualization_data(
            transaction_id,
            features,
            top_features,
        )
        plot = self.waterfall_plot(
            transaction_id,
            features,
            top_features,
        )
        rows = "".join(
            "<tr>"
            f"<td>{self._safe(point['feature'])}</td>"
            f"<td>{self._safe(point['feature_value'])}</td>"
            f"<td>{point['shap_value']:.6f}</td>"
            f"<td>{self._safe(point['direction'])}</td>"
            "</tr>"
            for point in local["points"]
        )
        global_section = ""
        if include_global_context:
            global_data = self.global_visualization_data(10)
            global_rows = "".join(
                "<tr>"
                f"<td>{item['rank']}</td>"
                f"<td>{self._safe(item['feature'])}</td>"
                f"<td>{item['importance']:.6f}</td>"
                "</tr>"
                for item in global_data["features"]
            )
            global_section = (
                "<h2>Global model context</h2>"
                f"<p>Samples used: {global_data['samples']}</p>"
                "<table><tr><th>Rank</th><th>Feature</th>"
                f"<th>Importance</th></tr>{global_rows}</table>"
            )

        document = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Fraud Explainability Report</title>
<style>
body {{ font-family: Arial; margin: 36px; color: #1f2937; }}
table {{ width: 100%; border-collapse: collapse; }}
th, td {{ border: 1px solid #d1d5db; padding: 8px; text-align: left; }}
th {{ background: #f3f4f6; }}
img {{ max-width: 100%; }}
</style>
</head>
<body>
<h1>Fraud Investigation Explainability Report</h1>
<p>Generated: {datetime.now(UTC).isoformat()}</p>
<p><b>Transaction:</b> {self._safe(transaction_id)} |
<b>Case:</b> {self._safe(case_id)}</p>
<p><b>Prediction:</b> {local['prediction']} |
<b>Probability:</b> {local['fraud_probability']:.4f} |
<b>Risk:</b> {self._safe(local['risk_band'])}</p>
<p>{self._safe(local['summary'])}</p>
<img alt="Local feature contributions"
src="data:image/png;base64,{plot['image_base64']}">
<table>
<tr><th>Feature</th><th>Value</th><th>SHAP</th><th>Direction</th></tr>
{rows}
</table>
<h2>Analyst notes</h2>
<p>{self._safe(analyst_notes) or 'No notes supplied.'}</p>
{global_section}
</body>
</html>
"""
        return document.encode("utf-8")

    def build_pdf_report(self, **kwargs: Any) -> bytes:
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.platypus import (
                Image,
                Paragraph,
                SimpleDocTemplate,
                Spacer,
                Table,
                TableStyle,
            )
        except ImportError as error:
            raise VisualizationServiceError(
                "PDF export requires reportlab>=4.2."
            ) from error

        transaction_id = kwargs["transaction_id"]
        features = kwargs["features"]
        top_features = kwargs.get("top_features", 10)
        local = self.local_visualization_data(
            transaction_id,
            features,
            top_features,
        )
        plot = self.waterfall_plot(
            transaction_id,
            features,
            top_features,
        )
        output = io.BytesIO()
        image_bytes = io.BytesIO(
            base64.b64decode(plot["image_base64"])
        )
        try:
            document = SimpleDocTemplate(output, pagesize=A4)
            styles = getSampleStyleSheet()
            story = [
                Paragraph(
                    "Fraud Investigation Explainability Report",
                    styles["Title"],
                ),
                Spacer(1, 8),
                Paragraph(
                    f"Transaction: {self._safe(transaction_id)}",
                    styles["BodyText"],
                ),
                Paragraph(
                    "Fraud probability: "
                    f"{local['fraud_probability']:.4f}",
                    styles["BodyText"],
                ),
                Image(image_bytes, width=440, height=211),
                Spacer(1, 10),
            ]
            table_data = [
                ["Feature", "Value", "SHAP", "Direction"]
            ] + [
                [
                    point["feature"],
                    str(point["feature_value"]),
                    f"{point['shap_value']:.6f}",
                    point["direction"],
                ]
                for point in local["points"]
            ]
            table = Table(table_data, repeatRows=1)
            table.setStyle(
                TableStyle(
                    [
                        (
                            "BACKGROUND",
                            (0, 0),
                            (-1, 0),
                            colors.lightgrey,
                        ),
                        (
                            "GRID",
                            (0, 0),
                            (-1, -1),
                            0.5,
                            colors.grey,
                        ),
                        ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ]
                )
            )
            story.extend(
                [
                    table,
                    Spacer(1, 10),
                    Paragraph("Analyst notes", styles["Heading2"]),
                    Paragraph(
                        self._safe(kwargs.get("analyst_notes"))
                        or "No notes supplied.",
                        styles["BodyText"],
                    ),
                ]
            )
            document.build(story)
            return output.getvalue()
        finally:
            image_bytes.close()
            output.close()

    def export_report(
        self,
        report_format: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        normalized_format = report_format.lower()
        if normalized_format == "html":
            content = self.build_html_report(**kwargs)
            media_type = "text/html"
        elif normalized_format == "pdf":
            content = self.build_pdf_report(**kwargs)
            media_type = "application/pdf"
        else:
            raise ValueError(
                "report_format must be 'html' or 'pdf'"
            )

        transaction_id = kwargs["transaction_id"]
        return {
            "transaction_id": transaction_id,
            "case_id": kwargs.get("case_id"),
            "report_format": normalized_format,
            "media_type": media_type,
            "filename": (
                f"fraud_explanation_{transaction_id}."
                f"{normalized_format}"
            ),
            "content_base64": base64.b64encode(content).decode(
                "ascii"
            ),
        }

    def health(self) -> dict[str, Any]:
        def service_status(service: Any) -> str:
            try:
                health_method = getattr(
                    service,
                    "health",
                    lambda: {"status": "ready"},
                )
                return str(
                    self._map(health_method()).get(
                        "status",
                        "ready",
                    )
                )
            except Exception:
                return "unavailable"

        local_status = service_status(self.local_service)
        global_status = service_status(self.global_service)
        return {
            "status": (
                "ready"
                if local_status == "ready"
                and global_status == "ready"
                else "degraded"
            ),
            "local_explainability": local_status,
            "global_explainability": global_status,
            "plotting_backend": matplotlib.get_backend(),
            "supported_plots": [
                "waterfall",
                "force",
                "summary_bar",
                "dependence_data",
            ],
            "supported_exports": ["html", "pdf"],
        }


explainability_visualization_service = (
    ExplainabilityVisualizationService()
)
