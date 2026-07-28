# Step 55 Integration

Copy the `frontend` folder into the repository root.

Register the route:

```jsx
import { TransactionExplorerPage } from "./features/transactionExplorer";

<Route path="/fraud/explorer" element={<TransactionExplorerPage />} />
```

Add navigation:

```jsx
<NavLink to="/fraud/explorer">Explorer</NavLink>
```

Verify from the project root:

```powershell
cd frontend
npm run test
npm run build
```

Suggested commit:

```powershell
git add frontend STEP55_INTEGRATION.md
git commit -m "Add transaction search and explorer"
git push origin dev
```
