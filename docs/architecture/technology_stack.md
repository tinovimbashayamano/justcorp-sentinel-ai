# Step 5: Technology Stack Justification

The JustCorp Sentinel AI platform will use a technology stack that supports machine learning, explainable AI, backend API development, structured data storage, reporting, containerisation, version control, and future deployment. The selected stack is suitable for a final-year AI and Machine Learning project, a GitHub portfolio project, and a production-oriented fraud intelligence prototype.

Python will be used as the main programming language because it is widely used for machine learning, data processing, backend development, and explainable AI workflows. It allows the project to use pandas, NumPy, scikit-learn, XGBoost, LightGBM, and SHAP within the same ecosystem.

FastAPI will be used for the backend API because the platform requires endpoints for authentication, transaction ingestion, fraud scoring, explanation retrieval, case review, dashboard metrics, and report generation. FastAPI is suitable because it works naturally with Python and provides automatic interactive API documentation, which will help with testing, demonstration, and integration.

PostgreSQL will be used as the primary database because the platform needs reliable structured storage for users, transactions, fraud predictions, SHAP explanations, investigation records, generated reports, and audit logs. PostgreSQL is appropriate because fraud intelligence data contains relationships between users, transactions, predictions, cases, reports, and system actions.

XGBoost and LightGBM will be used for fraud detection modelling because both are strong gradient-boosting algorithms for tabular data. They are suitable for financial transaction fraud detection because transaction datasets usually contain structured features such as transaction amount, timing, identity-related attributes, device behaviour, and account activity patterns.

SHAP will be used for explainable AI because the platform must not only predict fraud risk but also explain why a transaction was flagged. SHAP will support local explanations for individual transactions and global explanations showing the most influential features across the model.

pandas, NumPy, and scikit-learn will support data loading, cleaning, preprocessing, feature engineering, baseline modelling, model training, and model evaluation. These tools provide the foundation for building a reliable machine learning pipeline.

Docker will be used for containerisation so that the backend, database, and supporting services can run consistently across development, testing, and deployment environments. This reduces setup problems and supports future deployment.

Git and GitHub will be used for version control, collaboration, documentation, and portfolio presentation. GitHub Actions will later support automated testing and CI/CD workflows.

React + Vite will be introduced later for the dashboard frontend because the platform requires a professional user interface for fraud analysts, managers, auditors, and administrators. Frontend development will begin after the backend and machine learning foundation are stable.

## Alternatives Considered

Flask was considered as an alternative to FastAPI. Flask is simple and flexible, but FastAPI is preferred because this project needs structured API endpoints, request validation, and automatic API documentation for testing and demonstration.

SQLite was considered as an alternative to PostgreSQL. SQLite is easier to set up for small prototypes, but PostgreSQL is preferred because this project needs a more production-like relational database for storing users, transactions, predictions, explanations, investigation records, and audit logs.

Random Forest and Logistic Regression were considered as alternatives to XGBoost and LightGBM. Logistic Regression is useful as a simple baseline model, but it may not capture complex fraud patterns effectively. Random Forest can perform well on tabular data, but XGBoost and LightGBM are preferred for the main fraud detection engine because they are widely used gradient-boosting methods for high-performance structured data modelling.

LIME was considered as an alternative to SHAP. LIME can explain individual predictions, but SHAP is preferred because it provides both local and global explanations and is more suitable for building a consistent explainability layer for fraud investigation.

Streamlit was considered as an alternative to React + Vite for the user interface. Streamlit is useful for quick machine learning demos, but React + Vite is preferred for a more professional SaaS-style dashboard and portfolio-ready frontend.

Overall, the selected stack supports the project goal of building an explainable, audit-ready, API-accessible, and deployment-ready fraud intelligence platform.
