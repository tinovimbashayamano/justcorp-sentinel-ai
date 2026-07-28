import {
  formatAlertProbability,
} from "../domain/alertCenter";
import AlertSeverityBadge from "./AlertSeverityBadge";
import AlertTimeline from "./AlertTimeline";

function Detail({ label, value }) {
  return (
    <div className="alert-detail-item">
      <span>{label}</span>
      <strong>{value ?? "—"}</strong>
    </div>
  );
}

export default function AlertDrawer({
  alert,
  onClose,
  onAcknowledge,
  onInvestigate,
  onResolve,
  onExplain,
  onViewTransaction,
}) {
  if (!alert) return null;

  const shapSummary =
    alert.shap_summary ||
    alert.explanation_summary ||
    "Open Explainability to generate the SHAP summary.";

  return (
    <aside
      className="alert-drawer"
      aria-label="Fraud alert details"
    >
      <div className="alert-panel-header">
        <div>
          <p className="alert-eyebrow">Alert detail</p>
          <h2>
            {alert.transaction_id || `Alert ${alert.id}`}
          </h2>
        </div>
        <button type="button" onClick={onClose}>
          Close
        </button>
      </div>

      <div className="alert-drawer__headline">
        <AlertSeverityBadge severity={alert.severity} />
        <strong>{formatAlertProbability(alert)}</strong>
      </div>

      <div className="alert-detail-grid">
        <Detail label="Customer" value={alert.customer_id} />
        <Detail
          label="Merchant"
          value={alert.merchant_name || alert.merchant}
        />
        <Detail label="Risk" value={alert.risk_band} />
        <Detail label="Status" value={alert.alert_status} />
        <Detail
          label="Assigned analyst"
          value={alert.assigned_analyst}
        />
        <Detail label="Model version" value={alert.model_version} />
        <Detail
          label="Created"
          value={
            alert.created_at
              ? new Date(alert.created_at).toLocaleString()
              : null
          }
        />
      </div>

      <section className="alert-shap-summary">
        <p className="alert-eyebrow">SHAP summary</p>
        <p>{shapSummary}</p>
      </section>

      <AlertTimeline alert={alert} />

      <div className="alert-drawer-actions">
        {alert.alert_status === "unread" ? (
          <button
            type="button"
            onClick={() => onAcknowledge(alert.id)}
          >
            Acknowledge
          </button>
        ) : null}
        <button
          type="button"
          onClick={() => onViewTransaction(alert)}
        >
          View transaction
        </button>
        <button
          type="button"
          onClick={() => onInvestigate(alert)}
        >
          Investigate
        </button>
        <button
          type="button"
          onClick={() => onExplain(alert)}
        >
          View explanation
        </button>
        {alert.alert_status !== "resolved" ? (
          <button
            type="button"
            onClick={() => onResolve(alert.id)}
          >
            Dismiss
          </button>
        ) : null}
      </div>
    </aside>
  );
}
