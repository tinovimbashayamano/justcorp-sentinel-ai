# Step 50 — Frontend Explainability Investigation Workspace

## Objective

Integrate the Step 49 explainability API into the React and Vite
frontend.

## Architecture

- Feature-based module under `frontend/src/features/explainability`.
- Dedicated Axios API layer under `frontend/src/api`.
- Server-generated SHAP plots rendered from Base64 PNG responses.
- Browser Blob downloads for HTML/PDF investigation reports.
- A focused custom hook instead of global state infrastructure.

## Dependencies

```powershell
cd frontend
npm install axios
npm install -D vitest jsdom @testing-library/react @testing-library/jest-dom
```

## Environment

Create `frontend/.env`:

```text
VITE_API_BASE_URL=http://localhost:8000
```

## Route integration

```jsx
import { ExplainabilityWorkspace } from "./features/explainability";

<Route
  path="/fraud/explainability"
  element={<ExplainabilityWorkspace />}
/>
```

## Authentication

The client checks `localStorage.access_token` and
`localStorage.accessToken`. For another store:

```javascript
import { configureAccessTokenProvider } from "./api/httpClient";

configureAccessTokenProvider(
  () => authStore.getState().accessToken,
);
```

## Vitest

Add scripts:

```json
{
  "test": "vitest run",
  "test:watch": "vitest"
}
```

Configure Vite:

```javascript
test: {
  environment: "jsdom",
  setupFiles: "./vitest.setup.js",
  globals: true
}
```

## Verification

```powershell
npm run test
npm run build
```
