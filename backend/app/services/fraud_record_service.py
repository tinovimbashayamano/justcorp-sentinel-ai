from typing import Any

from sqlalchemy import desc
from sqlalchemy.orm import Session

from backend.app.models.fraud_score import FraudScoreRecord


def save_fraud_score_record(
    db: Session,
    transaction_id: str | None,
    scoring_result: dict[str, Any],
) -> FraudScoreRecord:
    record = FraudScoreRecord(
        transaction_id=transaction_id,
        model_name=scoring_result["model_name"],
        fraud_probability=scoring_result["fraud_probability"],
        fraud_prediction=scoring_result["fraud_prediction"],
        fraud_threshold=scoring_result["fraud_threshold"],
        risk_band=scoring_result["risk_band"],
        feature_quality=scoring_result["feature_quality"],
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    return record


def list_recent_fraud_scores(
    db: Session,
    limit: int = 20,
) -> list[FraudScoreRecord]:
    return (
        db.query(FraudScoreRecord)
        .order_by(desc(FraudScoreRecord.created_at))
        .limit(limit)
        .all()
    )
