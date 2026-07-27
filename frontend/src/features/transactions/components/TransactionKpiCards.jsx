const CARDS = [["total","Transactions"],["flagged","Flagged"],["critical","Critical"],["high","High risk"],["medium","Medium risk"]];
export default function TransactionKpiCards({ summary, onRiskSelect }) {
  return <section className="transaction-kpi-grid">{CARDS.map(([key,label]) => <button type="button" className="transaction-kpi-card" key={key} onClick={() => ["critical","high","medium"].includes(key) && onRiskSelect(key)}><span>{label}</span><strong>{summary[key] || 0}</strong></button>)}</section>;
}
