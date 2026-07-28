import { formatAlertProbability } from "../domain/alertCenter";
import AlertSeverityBadge from "./AlertSeverityBadge";
export default function AlertCard({ alert, selected, onSelect, onAcknowledge }) {
  return <article className={`alert-card ${selected ? "alert-card--selected" : ""}`}>
    <button type="button" className="alert-card__main" onClick={()=>onSelect(alert)}>
      <div className="alert-card__identity"><div><strong>{alert.transaction_id || `Alert ${alert.id}`}</strong><span>{alert.merchant_name || alert.merchant || alert.customer_id || "Unknown source"}</span></div><AlertSeverityBadge severity={alert.severity}/></div>
      <div className="alert-card__metrics"><strong>{formatAlertProbability(alert)}</strong><span>{alert.alert_status}</span></div>
    </button>
    {alert.alert_status === "unread" ? <button type="button" className="alert-card__acknowledge" onClick={()=>onAcknowledge(alert.id)}>Acknowledge</button> : null}
  </article>;
}
