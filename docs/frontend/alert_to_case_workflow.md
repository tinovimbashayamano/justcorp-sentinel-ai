# Step 52 — Alert-to-Case Workflow and Smart Investigation Queue

## Objective

Connect fraud score alerts to the case investigation workflow and provide
analysts with a searchable, sortable, paginated review queue.

## Scope

This stage is frontend-only and reuses the existing fraud case and score APIs.

## Architectural decisions

### Duplicate prevention

Before creating a case, the frontend checks whether a case already exists for
the selected `fraud_score_record_id`.

This prevents accidental duplicate requests during normal analyst use. A future
backend hardening stage should add a database uniqueness constraint because
frontend checks cannot protect against concurrent requests.

### Domain logic separated from React

Filtering, sorting, pagination, summaries and duplicate detection live in:

`frontend/src/features/cases/domain/caseQueue.js`

These pure functions are easy to test and keep business rules out of UI
components.

### Existing case workspace reused

Step 52 reuses the Step 51 `CaseSummary`, `CaseEditor` and
`CaseExplainabilityLink` components instead of creating a second investigation
form.

### Client-side queue operations

The current API exposes list endpoints but no documented server-side search,
pagination or multi-filter contract. Step 52 therefore applies queue operations
client-side over the loaded records.

When the dataset becomes too large, the next backend enhancement should add
server-side pagination, indexed filtering and stable sorting.

## Route integration

```jsx
import { SmartInvestigationQueuePage } from "./features/cases";

<Route
  path="/fraud/investigations"
  element={<SmartInvestigationQueuePage />}
/>
```

## Dashboard integration

Dashboard fraud-alert actions should navigate to:

```text
/fraud/investigations
```

A later enhancement may pass a score ID through router state or a query
parameter for automatic opening.

## Verification

```powershell
cd frontend
npm run test
npm run build
```
