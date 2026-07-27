import {
  NavLink,
  Route,
  Routes,
} from "react-router";

import { ExplainabilityWorkspace } from "./features/explainability";
import "./app.css";

const EXPLAINABILITY_ROLES = new Set([
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
  const canViewExplainability =
    EXPLAINABILITY_ROLES.has(
      String(readStoredRole() || "").toLowerCase(),
    );

  return (
    <>
      <nav
        className="app-navigation"
        aria-label="Primary navigation"
      >
        <NavLink to="/">Sentinel AI</NavLink>
        {canViewExplainability ? (
          <NavLink to="/fraud/explainability">
            Explainability
          </NavLink>
        ) : null}
      </nav>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route
          path="/fraud/explainability"
          element={<ExplainabilityWorkspace />}
        />
        <Route path="*" element={<HomePage />} />
      </Routes>
    </>
  );
}
