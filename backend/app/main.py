from fastapi import FastAPI


app = FastAPI(
    title="JustCorp Sentinel AI",
    description=(
        "Explainable Fraud Intelligence Platform for financial transaction"
        " risk scoring."
    ),
    version="0.1.0",
)


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

