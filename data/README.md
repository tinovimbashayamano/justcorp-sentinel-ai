JustCorp Sentinel AI

JustCorp Sentinel AI is an explainable fraud intelligence platform for FinTech, microfinance, insurance, and risk analytics use cases.

The platform is designed to detect potentially fraudulent financial transactions, generate fraud risk scores, explain model decisions using explainable AI methods, support fraud investigation workflows, and produce structured reports for review and decision-making.

Project Status

Current phase: Phase 1 — Project Foundation
Current step completed: Docker Setup
Current backend status: FastAPI health endpoint running locally and through Docker

Core Objectives
Detect potentially fraudulent financial transactions
Generate fraud risk scores for submitted transactions
Explain fraud predictions using SHAP-based explainability
Store transactions, predictions, explanations, reports, and review actions
Support fraud analyst investigation workflows
Provide REST APIs for transaction ingestion and fraud scoring
Generate audit-ready PDF and Excel reports
Prepare the platform for deployment and future SaaS productisation
Technology Stack
Backend
Python
FastAPI
PostgreSQL
SQLAlchemy
Alembic
JWT authentication later
Machine Learning
pandas
NumPy
scikit-learn
XGBoost
LightGBM
SHAP
imbalanced-learn
Infrastructure
Docker
Docker Compose
GitHub
GitHub Actions later
Nginx later
Frontend
React + Vite later
Current Features Implemented
Project repository structure
GitHub main and dev branches
Python virtual environment setup
FastAPI backend scaffold
Root endpoint
Health-check endpoint
Docker backend container
PostgreSQL Docker container
Docker Compose setup