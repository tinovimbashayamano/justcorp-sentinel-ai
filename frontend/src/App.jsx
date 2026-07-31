import { lazy, Suspense } from "react";
import {
  Link,
  Navigate,
  NavLink,
  Route,
  Routes,
  useLocation,
} from "react-router";

import { useAlertCenter } from "./features/alerts/hooks/useAlertCenter";
import PageLoading from "./components/PageLoading";
import "./app.css";

const CaseInvestigationWorkspace = lazy(() =>
  import("./features/cases/pages/CaseInvestigationWorkspace")
);
const SmartInvestigationQueuePage = lazy(() =>
  import("./features/cases/pages/SmartInvestigationQueuePage")
);
const FraudAlertCenterPage = lazy(() =>
  import("./features/alerts/pages/FraudAlertCenterPage")
);
const AdminPortalPage = lazy(() =>
  import("./features/admin/pages/AdminPortalPage")
);
const AuditTrailPage = lazy(() =>
  import("./features/auditTrail/pages/AuditTrailPage")
);
const ExplainabilityWorkspace = lazy(() =>
  import("./features/explainability/pages/ExplainabilityWorkspace")
);
const InvestigationWorkspacePage = lazy(() =>
  import("./features/investigationWorkspace/pages/InvestigationWorkspacePage")
);
const ModelGovernancePage = lazy(() =>
  import("./features/modelGovernance/pages/ModelGovernancePage")
);
const OperationsDashboardPage = lazy(() =>
  import("./features/operations/pages/OperationsDashboardPage")
);
const PreferencesPage = lazy(() =>
  import("./features/preferences/pages/PreferencesPage")
);
const ReportingDashboardPage = lazy(() =>
  import("./features/reporting/pages/ReportingDashboardPage")
);
const ReportExportDashboard = lazy(() =>
  import("./features/reports/pages/ReportExportDashboard")
);
const TransactionExplorerPage = lazy(() =>
  import("./features/transactionExplorer/pages/TransactionExplorerPage")
);
const TransactionMonitoringPage = lazy(() =>
  import("./features/transactions/pages/TransactionMonitoringPage")
);

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

const AUDIT_TRAIL_ROLES = new Set([
  "admin",
  "administrator",
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
  const canViewAuditTrail =
    isAuthenticated && AUDIT_TRAIL_ROLES.has(storedRole);
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
            <>
              <NavLink to="/reports">
                Reports
              </NavLink>
              <NavLink to="/reports/export">
                Report Exports
              </NavLink>
            </>
          ) : null}
          {canViewOperations ? (
            <NavLink to="/operations">
              Operations
            </NavLink>
          ) : null}
          {canViewAuditTrail ? (
            <NavLink to="/audit-trail">
              Audit Trail
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
      <Suspense fallback={<PageLoading />}>
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
          path="/reports/export"
          element={
            canViewReports ? (
              <ReportExportDashboard />
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
          path="/audit-trail"
          element={
            canViewAuditTrail ? (
              <AuditTrailPage />
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
      </Suspense>
    </>
  );
}
