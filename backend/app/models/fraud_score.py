from sqlalchemy import DateTime, Float, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.session import Base


class FraudScoreRecord(Base):
    __tablename__ = "fraud_score_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    transaction_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )

    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    fraud_probability: Mapped[float] = mapped_column(Float, nullable=False)
    fraud_prediction: Mapped[int] = mapped_column(Integer, nullable=False)
    fraud_threshold: Mapped[float] = mapped_column(Float, nullable=False)
    risk_band: Mapped[str] = mapped_column(String(30), nullable=False)

    feature_quality: Mapped[dict] = mapped_column(JSON, nullable=False)

    created_at = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
