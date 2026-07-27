# Step 51 — Fraud Case Investigation Workspace

## Objective

Connect the React frontend to the existing fraud case review workflow.

The backend already exposes:

- `GET /api/v1/fraud/cases`
- `GET /api/v1/fraud/cases/{case_id}`
- `POST /api/v1/fraud/cases`
- `PATCH /api/v1/fraud/cases/{case_id}`
- `GET /api/v1/fraud/scores`

## Architectural decisions

### Existing backend reused

No new backend route is introduced. This stage integrates with the case
review workflow already implemented in the fraud router.

### Queue/detail layout

The page uses a queue on the left and a selected-case workspace on the
right. This pattern scales better than rendering a full editor for every
case.

### Server remains the source of truth

After a case update, the frontend replaces the local case with the
response returned by the API. It does not invent timestamps or status
transitions.

### Explainability is linked, not duplicated

The case page links to the Step 50 explainability workspace instead of
embedding a second copy of the explainability feature.

## Route integration

```jsx
import { CaseInvestigationWorkspace } from "./features/cases";

<Route
  path="/fraud/cases"
  element={<CaseInvestigationWorkspace />}
/>
```

## Navigation

Show the route to roles allowed to review fraud cases, typically admin
and fraud analyst. Backend RBAC remains the security boundary.

## Verification

```powershell
cd frontend
npm run test
npm run build
```

Manual verification:

1. Case queue loads.
2. Selecting a case loads its complete record.
3. Linked fraud score details appear.
4. Status, decision, reviewer, and notes can be updated.
5. The selected case remains synchronized after save.
6. Explainability link opens the Step 50 workspace.
7. Unauthenticated requests remain blocked by the backend.
