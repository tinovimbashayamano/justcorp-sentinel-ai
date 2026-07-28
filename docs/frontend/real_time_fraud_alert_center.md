# Step 54 — Real-Time Fraud Alert Center

This frontend stage polls `GET /api/v1/fraud/scores` every 30 seconds and turns score records into alert cards. Alert acknowledgement, investigation, and resolution states are stored in browser local storage because no persistent backend alert workflow endpoint has yet been defined.

For production multi-user operation, add persistent alert records, assignment and acknowledgement endpoints, audit events, and WebSocket or Server-Sent Events delivery.

## Route

```jsx
import { FraudAlertCenterPage } from "./features/alerts";
<Route path="/fraud/alerts" element={<FraudAlertCenterPage />} />
```

## Verification

```powershell
cd frontend
npm run test
npm run build
```
