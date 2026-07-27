import {
  NavLink,
  Route,
  Routes,
} from "react-router";

import {
  CaseInvestigationWorkspace,
  SmartInvestigationQueuePage,
} from "./features/cases";
import { ExplainabilityWorkspace } from "./features/explainability";
import { TransactionMonitoringPage } from "./features/transactions";
import "./app.css";

const REVIEW_ROLES = new Set([
  "admin",
  "fraud_analyst",
]);

function readStoredRole() {
  const directRole =
    window.localStorage.getItem("user_role") ||
    window.localStorage.getItem("userRole") ||
    window.localStorage.getItem("role");
  if (directRole) return directRole;

  try {
    const user = JSON.parse(
      window.localStorage.getItem("user") || "null",
    );
    return user?.role || null;
  } catch {
    return null;
  }
}

function HomePage() {
  return (
    <main className="home-page">
      <p className="app-eyebrow">
        JustCorp Sentinel AI
      </p>
      <h1>Fraud intelligence workspace</h1>
      <p>
        Review model decisions and investigate financial
        transaction risk.
      </p>
    </main>
  );
}

export default function App() {
  const canReviewCases = REVIEW_ROLES.has(
    String(readStoredRole() || "").toLowerCase(),
  );
  const canMonitorTransactions = canReviewCases;
  const canInvestigate = canReviewCases;
  const canViewExplainability = canReviewCases;

  return (
    <>
      <nav
        className="app-navigation"
        aria-label="Primary navigation"
      >
        <NavLink to="/">Sentinel AI</NavLink>
        <div className="app-navigation__links">
          {canMonitorTransactions ? (
            <NavLink to="/fraud/transactions">
              Transactions
            </NavLink>
          ) : null}
          {canInvestigate ? (
            <NavLink to="/fraud/investigations">
              Investigations
            </NavLink>
          ) : null}
          {canReviewCases ? (
            <NavLink to="/fraud/cases">
              Review Queue
            </NavLink>
          ) : null}
          {canViewExplainability ? (
            <NavLink to="/fraud/explainability">
              Explainability
            </NavLink>
          ) : null}
        </div>
      </nav>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route
          path="/fraud/cases"
          element={<CaseInvestigationWorkspace />}
        />
        <Route
          path="/fraud/transactions"
          element={<TransactionMonitoringPage />}
        />
        <Route
          path="/fraud/investigations"
          element={<SmartInvestigationQueuePage />}
        />
        <Route
          path="/fraud/explainability"
          element={<ExplainabilityWorkspace />}
        />
        <Route path="*" element={<HomePage />} />
      </Routes>
    </>
  );
}
