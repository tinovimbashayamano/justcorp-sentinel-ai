# Analytics and Executive Dashboard

## Purpose

The analytics subsystem provides read-only fraud intelligence for executive,
operational, investigation, and governance users. It converts persisted fraud
scores and fraud-case workflow data into dashboard-ready API responses.

## Architecture

```text
Analytics API
     |
     v
Analytics Service
     |
     v
Analytics Repository
     |
     v
PostgreSQL fraud scores, cases, and users
```

The API performs authentication, role checks, query-parameter validation, and
response serialization. Business calculations remain in the service, while
SQL aggregation remains in the repository.

## Data sources

The current implementation reads:

- `fraud_score_records`
- `fraud_case_reviews`
- `users`, for investigator names

It does not create analytics tables or require a database migration.

## Repository responsibilities

`AnalyticsRepository`:

- Validates and normalizes UTC date ranges
- Aggregates fraud totals and average fraud probabilities
- Groups transactions by persisted risk band
- Returns daily fraud-score trends
- Retrieves high and critical-risk transactions
- Aggregates fraud cases by status and investigator
- Associates fraud-score records with cases
- Reports source availability and latest timestamps

Repository operations are read-only.

## Service responsibilities

`AnalyticsService`:

- Builds executive KPIs
- Calculates percentages and rates
- Normalizes risk-band values
- Builds fraud-score histograms
- Converts daily SQL date buckets into UTC datetimes
- Produces case and investigator performance responses
- Maps high-risk records to API-safe schemas
- Builds the combined dashboard response
- Preserves explicit zero or null values for unsupported metrics

## API endpoints

All endpoints use the `/api/v1/analytics` prefix:

- `GET /health`
- `GET /dashboard`
- `GET /executive-kpis`
- `GET /risk-distribution`
- `GET /fraud-score-distribution`
- `GET /fraud-trend`
- `GET /case-status-distribution`
- `GET /investigator-performance`
- `GET /high-risk-transactions`

Date-filtered endpoints accept optional `start_at` and `end_at` UTC
timestamps. High-risk results support `limit` and `offset`.

## Supported KPIs

The executive response currently includes:

- Total, fraudulent, and legitimate transaction counts
- Fraud rate
- Average fraud score
- High and critical-risk transaction counts
- Total, open, closed, and escalated case counts
- Resolution and escalation rates

Escalated case counts remain zero until an explicit persisted escalation field
or event projection is available.

## Risk bands

The normalized risk levels are:

- `low`: fraud score from 0.00 through 0.30
- `medium`: above 0.30 through 0.60
- `high`: above 0.60 through 0.85
- `critical`: above 0.85 through 1.00

The distribution endpoint uses the risk band persisted with each fraud-score
record. Unknown persisted values are normalized to `low` by the service.

## Daily trend behavior

The current bundle supports daily grouping only. SQL `date()` grouping is
used because it behaves consistently across PostgreSQL and the SQLite test
database. Requests for hourly, weekly, or monthly grouping return HTTP 422.

Daily points report transaction counts, fraudulent counts, legitimate counts,
fraud rate, and average fraud score.

## RBAC

Authentication is required. Analytics access is allowed to these operational
and governance role names:

- `admin`
- `fraud_analyst`
- `analyst`
- `risk_manager`
- `manager`
- `auditor`

The current `UserRole` model directly defines `admin`, `fraud_analyst`, and
`auditor`. Viewers are denied with HTTP 403.

## Financial-data limitation

Transaction amount, protected amount, product code, and original transaction
timestamp are not currently persisted in `FraudScoreRecord`. Financial
analytics therefore return zero or null rather than inferred values.

Specifically:

- Executive amount metrics return `0`
- Risk-distribution transaction amounts return `0`
- Trend transaction and fraudulent amounts return `0`
- High-risk transaction amounts and product codes return `null`
- The fraud-score creation timestamp is exposed only where the response
  requires the currently available transaction date

## Explainability-data limitation

The model currently stores feature-quality JSON but does not persist
queryable SHAP values or per-feature contribution records. Explainability
availability is therefore reported as `false`, and aggregated feature
importance is not fabricated.

## Future improvements

- Persist transaction amount, currency, product code, and event timestamp
- Persist explicit case escalation and resolution timestamps
- Add hourly, weekly, and monthly trend grouping
- Persist model explainability contributions
- Add materialized views for large analytics workloads
- Add caching for executive dashboard responses
- Add exportable analytics reports
- Add configurable risk-band thresholds
- Add asynchronous dashboard refresh jobs
