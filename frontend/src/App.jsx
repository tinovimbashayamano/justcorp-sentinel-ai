import {
  Link,
  Navigate,
  NavLink,
  Route,
  Routes,
  useLocation,
} from "react-router";

import {
  CaseInvestigationWorkspace,
  SmartInvestigationQueuePage,
} from "./features/cases";
import {
  FraudAlertCenterPage,
  useAlertCenter,
} from "./features/alerts";
import { AdminPortalPage } from "./features/admin";
import { ExplainabilityWorkspace } from "./features/explainability";
import { InvestigationWorkspacePage } from "./features/investigationWorkspace";
import { ModelGovernancePage } from "./features/modelGovernance";
import { OperationsDashboardPage } from "./features/operations";
import { PreferencesPage } from "./features/preferences";
import { ReportingDashboardPage } from "./features/reporting";
import { TransactionExplorerPage } from "./features/transactionExplorer";
import { TransactionMonitoringPage } from "./features/transactions";
import "./app.css";

const REVIEW_ROLES = new Set([
  "admin",
  "fraud_analyst",
]);

const REPORT_ROLES = new Set([
  "admin",
  "administrator",
  "risk_manager",
  "manager",
  "auditor",
]);

const OPERATIONS_ROLES = new Set([
  "admin",
  "administrator",
  "technical_lead",
  "auditor",
]);

const MODEL_GOVERNANCE_ROLES = new Set([
  "admin",
  "administrator",
  "data_scientist",
  "risk_manager",
  "manager",
  "compliance_officer",
  "technical_lead",
  "auditor",
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

function hasStoredAccessToken() {
  return Boolean(
    window.localStorage.getItem("access_token") ||
      window.localStorage.getItem("accessToken"),
  );
}

function HomePage({
  alertSummary,
  canViewAlerts,
}) {
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
      {canViewAlerts ? (
        <div className="home-page__alert-cards">
          <Link to="/fraud/alerts?severity=critical">
            <span>Critical alerts</span>
            <strong>{alertSummary.critical}</strong>
          </Link>
          <Link to="/fraud/alerts?status=unread">
            <span>Unread alerts</span>
            <strong>{alertSummary.unread}</strong>
          </Link>
        </div>
      ) : null}
    </main>
  );
}

export default function App() {
  const location = useLocation();
  const isAdminRoute = location.pathname === "/admin";
  const storedRole = String(
    readStoredRole() || "",
  ).toLowerCase();
  const isAdministrator =
    storedRole === "admin" || storedRole === "administrator";
  const isAuthenticated = hasStoredAccessToken();
  const canReviewCases = REVIEW_ROLES.has(
    storedRole,
  );
  const canViewAlerts = canReviewCases;
  const canExploreTransactions = canReviewCases;
  const canMonitorTransactions = canReviewCases;
  const canInvestigate = canReviewCases;
  const canViewExplainability = canReviewCases;
  const canViewReports = REPORT_ROLES.has(storedRole);
  const canViewOperations = OPERATIONS_ROLES.has(storedRole);
  const canViewModelGovernance =
    isAuthenticated && MODEL_GOVERNANCE_ROLES.has(storedRole);
  const alertCenter = useAlertCenter({
    enabled: canViewAlerts,
  });

  return (
    <>
      <nav
        className={
          isAdminRoute
            ? "app-navigation app-navigation--hidden"
            : "app-navigation"
        }
        aria-label="Primary navigation"
      >
        <NavLink to="/">Sentinel AI</NavLink>
        <div className="app-navigation__links">
          {canViewAlerts ? (
            <NavLink
              className="app-navigation__alert-link"
              to="/fraud/alerts"
            >
              <span>Alerts</span>
              <span className="app-navigation__alert-count">
                {alertCenter.summary.total}
              </span>
              <span className="app-navigation__unread-count">
                {alertCenter.summary.unread} unread
              </span>
            </NavLink>
          ) : null}
          {canMonitorTransactions ? (
            <NavLink to="/fraud/transactions">
              Transactions
            </NavLink>
          ) : null}
          {canExploreTransactions ? (
            <NavLink to="/fraud/explorer">
              Explorer
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
          {canViewReports ? (
            <NavLink to="/reports">
              Reports
            </NavLink>
          ) : null}
          {canViewOperations ? (
            <NavLink to="/operations">
              Operations
            </NavLink>
          ) : null}
          {canViewModelGovernance ? (
            <NavLink to="/model-governance">
              Model Governance
            </NavLink>
          ) : null}
          {isAuthenticated ? (
            <NavLink to="/preferences">
              Preferences
            </NavLink>
          ) : null}
          {isAdministrator ? (
            <NavLink to="/admin">
              Administration
            </NavLink>
          ) : null}
        </div>
      </nav>
      <Routes>
        <Route
          path="/"
          element={
            <HomePage
              alertSummary={alertCenter.summary}
              canViewAlerts={canViewAlerts}
            />
          }
        />
        <Route
          path="/fraud/cases"
          element={<CaseInvestigationWorkspace />}
        />
        <Route
          path="/fraud/alerts"
          element={
            <FraudAlertCenterPage
              alertCenter={
                canViewAlerts ? alertCenter : null
              }
            />
          }
        />
        <Route
          path="/fraud/transactions"
          element={<TransactionMonitoringPage />}
        />
        <Route
          path="/fraud/explorer"
          element={<TransactionExplorerPage />}
        />
        <Route
          path="/fraud/investigations"
          element={<SmartInvestigationQueuePage />}
        />
        <Route
          path="/fraud/investigations/:caseId"
          element={<InvestigationWorkspacePage />}
        />
        <Route
          path="/fraud/explainability"
          element={<ExplainabilityWorkspace />}
        />
        <Route
          path="/reports"
          element={
            canViewReports ? (
              <ReportingDashboardPage />
            ) : (
              <Navigate to="/" replace />
            )
          }
        />
        <Route
          path="/operations"
          element={
            canViewOperations ? (
              <OperationsDashboardPage />
            ) : (
              <Navigate to="/" replace />
            )
          }
        />
        <Route
          path="/preferences"
          element={
            isAuthenticated ? (
              <PreferencesPage />
            ) : (
              <Navigate to="/" replace />
            )
          }
        />
        <Route
          path="/model-governance"
          element={
            canViewModelGovernance ? (
              <ModelGovernancePage />
            ) : (
              <Navigate to="/" replace />
            )
          }
        />
        <Route
          path="/admin"
          element={
            isAdministrator ? (
              <AdminPortalPage />
            ) : (
              <Navigate to="/" replace />
            )
          }
        />
        <Route
          path="*"
          element={
            <HomePage
              alertSummary={alertCenter.summary}
              canViewAlerts={canViewAlerts}
            />
          }
        />
      </Routes>
    </>
  );
}
