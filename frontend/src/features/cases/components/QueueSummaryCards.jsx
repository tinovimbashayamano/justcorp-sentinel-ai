const CARDS = [
  ["open", "Open"],
  ["under_review", "Under review"],
  ["confirmed_fraud", "Confirmed fraud"],
  ["false_positive", "False positives"],
  ["closed", "Closed"],
];

export default function QueueSummaryCards({
  summary,
  onStatusSelect,
}) {
  return (
    <section
      className="queue-summary-grid"
      aria-label="Case queue summary"
    >
      {CARDS.map(([key, label]) => (
        <button
          className="queue-summary-card"
          type="button"
          key={key}
          onClick={() => onStatusSelect(key)}
        >
          <span>{label}</span>
          <strong>{summary[key] || 0}</strong>
        </button>
      ))}
    </section>
  );
}
