from backend.app.db.session import Base, engine
from backend.app.models.fraud_case import FraudCaseReview
from backend.app.models.fraud_score import FraudScoreRecord


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully.")
    print(f"Registered table: {FraudScoreRecord.__tablename__}")
    print(f"Registered table: {FraudCaseReview.__tablename__}")


if __name__ == "__main__":
    init_db()
