from fastapi import FastAPI

from backend.app.api.admin_users import router as admin_users_router
from backend.app.api.auth import router as auth_router
from backend.app.api.fraud import router as fraud_router


app = FastAPI(
    title="JustCorp Sentinel AI",
    description=(
        "Explainable Fraud Intelligence Platform for financial transaction"
        " risk scoring."
    ),
    version="0.1.0",
)

app.include_router(auth_router)
app.include_router(fraud_router)
app.include_router(admin_users_router)


@app.get("/")
def read_root():
    return {
        "message": "JustCorp Sentinel AI backend is running",
        "status": "ok",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "justcorp-sentinel-ai-backend",
    }
