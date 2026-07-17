from backend.app.db.session import Base, engine
from backend.app.models.fraud_case import FraudCaseReview
from backend.app.models.fraud_score import FraudScoreRecord
from backend.app.models.refresh_token import RefreshToken
from backend.app.models.user import User


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully.")
    print(f"Registered table: {FraudScoreRecord.__tablename__}")
    print(f"Registered table: {FraudCaseReview.__tablename__}")
    print(f"Registered table: {User.__tablename__}")
    print(f"Registered table: {RefreshToken.__tablename__}")


if __name__ == "__main__":
    init_db()
