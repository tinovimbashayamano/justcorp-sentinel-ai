import { useEffect } from "react";
import {
  useLocation,
  useNavigate,
} from "react-router";

import AlertCenter from "../components/AlertCenter";
import AlertDrawer from "../components/AlertDrawer";
import AlertFilters from "../components/AlertFilters";
import AlertStatistics from "../components/AlertStatistics";
import AlertToolbar from "../components/AlertToolbar";
import {
  ALERT_SEVERITIES,
  ALERT_STATUSES,
} from "../domain/alertCenter";
import { useAlertCenter } from "../hooks/useAlertCenter";
import "../styles/fraud-alert-center.css";

function readStoredAnalyst() {
  try {
    const user = JSON.parse(
      window.localStorage.getItem("user") || "null",
    );
    return (
      user?.name ||
      user?.username ||
      user?.email ||
      null
    );
  } catch {
    return null;
  }
}

export default function FraudAlertCenterPage({
  alertCenter: sharedAlertCenter = null,
}) {
  const location = useLocation();
  const navigate = useNavigate();
  const localAlertCenter = useAlertCenter({
    enabled: !sharedAlertCenter,
  });
  const {
    visibleAlerts,
    selectedAlert,
    filters,
    sort,
    summary,
    pagination,
    loading,
    error,
    loadAlerts,
    setSelectedAlert,
    updateStatus,
    updateFilters,
    clearFilters,
    setSort,
    setPage,
  } = sharedAlertCenter || localAlertCenter;

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const severity = params.get("severity") || "";
    const status = params.get("status") || "";
    const patch = {};

    if (ALERT_SEVERITIES.includes(severity)) {
      patch.severity = severity;
    }
    if (ALERT_STATUSES.includes(status)) {
      patch.status = status;
    }
    if (Object.keys(patch).length) {
      updateFilters(patch);
    }
  }, [location.search, updateFilters]);

  function selectStat(key) {
    if (ALERT_SEVERITIES.includes(key)) {
      updateFilters({ severity: key });
    } else {
      updateFilters({ status: key });
    }
  }

  function investigate(alert) {
    updateStatus(
      alert.id,
      "investigating",
      alert.assigned_analyst || readStoredAnalyst(),
    );
    navigate("/fraud/investigations", {
      state: {
        fraudScoreRecordId: alert.id,
        transactionId: alert.transaction_id,
      },
    });
  }

  function explain(alert) {
    navigate(
      `/fraud/explainability?scoreId=${alert.id}`,
      {
        state: {
          fraudScoreRecordId: alert.id,
          transactionId: alert.transaction_id,
        },
      },
    );
  }

  function viewTransaction(alert) {
    navigate(`/fraud/transactions?scoreId=${alert.id}`, {
      state: {
        fraudScoreRecordId: alert.id,
        transactionId: alert.transaction_id,
      },
    });
  }

  return (
    <main className="fraud-alert-center-page">
      <header className="alert-page-header">
        <div>
          <p className="alert-eyebrow">
            JustCorp Sentinel AI
          </p>
          <h1>Fraud Alert Center</h1>
          <p>
            Monitor high-risk activity, acknowledge alerts,
            and escalate suspicious transactions into formal
            investigations.
          </p>
        </div>
      </header>

      {error ? (
        <div className="alert-error" role="alert">
          {error.message}
        </div>
      ) : null}

      <AlertToolbar
        summary={summary}
        pagination={pagination}
        loading={loading}
        onRefresh={loadAlerts}
        onPageChange={setPage}
      />
      <AlertStatistics
        summary={summary}
        onSelect={selectStat}
      />
      <AlertFilters
        filters={filters}
        sort={sort}
        onFiltersChange={updateFilters}
        onSortChange={setSort}
        onClear={clearFilters}
      />
      <AlertCenter
        alerts={visibleAlerts}
        selectedAlertId={selectedAlert?.id}
        loading={loading}
        onSelect={setSelectedAlert}
        onAcknowledge={(id) =>
          updateStatus(id, "acknowledged")
        }
      />
      <AlertDrawer
        alert={selectedAlert}
        onClose={() => setSelectedAlert(null)}
        onAcknowledge={(id) =>
          updateStatus(id, "acknowledged")
        }
        onInvestigate={investigate}
        onResolve={(id) => updateStatus(id, "resolved")}
        onExplain={explain}
        onViewTransaction={viewTransaction}
      />
    </main>
  );
}
