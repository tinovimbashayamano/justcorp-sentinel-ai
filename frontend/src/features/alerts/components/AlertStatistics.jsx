const CARDS = [["unread", "Unread"], ["critical", "Critical"], ["high", "High"], ["investigating", "Investigating"], ["resolved", "Resolved"]];
export default function AlertStatistics({ summary, onSelect }) {
  return <section className="alert-stat-grid">{CARDS.map(([key,label]) => <button type="button" className="alert-stat-card" key={key} onClick={() => onSelect(key)}><span>{label}</span><strong>{summary[key] || 0}</strong></button>)}</section>;
}
