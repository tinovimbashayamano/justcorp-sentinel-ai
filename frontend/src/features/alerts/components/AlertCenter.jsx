import AlertCard from "./AlertCard";
export default function AlertCenter({ alerts, selectedAlertId, loading, onSelect, onAcknowledge }) {
  return <section className="alert-center-panel"><div className="alert-panel-header"><div><p className="alert-eyebrow">Live alert feed</p><h2>Fraud alerts</h2></div><span>{alerts.length} shown</span></div>{loading ? <p>Loading alerts…</p> : alerts.length === 0 ? <p>No alerts match the current filters.</p> : <div className="alert-card-list">{alerts.map((alert)=><AlertCard key={alert.id} alert={alert} selected={selectedAlertId===alert.id} onSelect={onSelect} onAcknowledge={onAcknowledge}/>)}</div>}</section>;
}
