# Step 3: System Requirements

The JustCorp Sentinel AI platform must deliver the technical capabilities needed to detect, explain, store, review, and report potentially fraudulent financial transactions. These system requirements are divided into functional requirements and non-functional requirements.

## 3.1 Functional Requirements

### Functional Requirement 1: User Authentication

The system must enable users to log in securely before accessing protected platform features. This ensures that only authorised users can view transaction data, fraud scores, explanations, and reports.

### Functional Requirement 2: Role-Based Access Control

The system must support distinct user roles such as administrator, fraud analyst, risk officer, manager, and auditor. Each role should be granted access only to the features and data relevant to their responsibilities.

### Functional Requirement 3: Transaction Data Ingestion

The system must accept transaction data submissions through an API. Incoming data must include the fields required by the fraud detection model to produce a prediction.

### Functional Requirement 4: Fraud Risk Scoring

The system must process incoming transaction data and return a fraud risk prediction or score, indicating whether a transaction appears legitimate or suspicious.

### Functional Requirement 5: Explainable AI Output

The system must generate explanations for fraud predictions, highlighting the key transaction features that influenced the model’s decision.

### Functional Requirement 6: Transaction Storage

The system must store submitted transaction records, fraud scores, prediction outcomes, explanation outputs, and timestamps in a database.

### Functional Requirement 7: Fraud Case Review

The system must allow authorised users to review suspicious transactions, update their investigation status, and record analyst comments or decisions.

### Functional Requirement 8: Report Generation

The system must produce structured fraud reports containing transaction details, fraud scores, explanation summaries, investigation notes, and review outcomes.

### Functional Requirement 9: Dashboard Metrics

The system must present summary metrics such as total transactions processed, number of suspicious transactions, fraud risk distribution, and model performance indicators.

### Functional Requirement 10: API Documentation

The system must provide clear API documentation so that developers and external systems can understand how to submit transactions and retrieve fraud risk results.

## 3.2 Non-Functional Requirements

### Non-Functional Requirement 1: Security

The system must safeguard sensitive transaction data through authentication, controlled access, secure password handling, and secure API design.

### Non-Functional Requirement 2: Performance

The system should return fraud scoring results within 1–3 seconds for a single transaction under normal demonstration conditions, supporting real-time or near-real-time use.

### Non-Functional Requirement 3: Reliability

The system should handle errors gracefully and provide meaningful error messages when invalid data is submitted or when system operations fail.

### Non-Functional Requirement 4: Scalability

The system should be designed to accommodate future growth, including additional users, higher transaction volumes, multiple organisations, and more advanced deployment configurations.

### Non-Functional Requirement 5: Maintainability

The codebase should follow a well-organised folder structure, use readable naming conventions, include documentation, and maintain clear separation between major responsibilities such as API routes, database models, machine learning logic, and reporting logic.

### Non-Functional Requirement 6: Traceability

The system must maintain records of transaction submissions, prediction results, user actions, and generated reports so that fraud-related decisions remain auditable over time.

### Non-Functional Requirement 7: Explainability

The system must deliver explanations that are understandable enough for fraud analysts, risk officers, and auditors to interpret effectively.

### Non-Functional Requirement 8: Portability

The system should be containerised so that it can run consistently across development, testing, and production environments.

### Non-Functional Requirement 9: Availability

The system should be designed for deployment in a way that supports continuous access during demonstrations, testing, and future production use.

### Non-Functional Requirement 10: Compliance Awareness

The system should be built with awareness of audit, privacy, and responsible AI expectations. It must support documentation and review processes, but it should not be represented as a legally certified compliance system.
