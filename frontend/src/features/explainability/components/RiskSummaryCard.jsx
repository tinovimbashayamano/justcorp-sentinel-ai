function formatProbability(value) {
  return new Intl.NumberFormat("en-US", {
    style: "percent",
    maximumFractionDigits: 2,
  }).format(Number(value || 0));
}

export default function RiskSummaryCard({
  explanation,
}) {
  if (!explanation) {
    return (
      <section className="panel panel--empty">
        Select or enter a transaction to generate an
        explanation.
      </section>
    );
  }

  return (
    <section
      className="panel"
      aria-labelledby="risk-summary-title"
    >
      <div className="panel__header">
        <div>
          <p className="eyebrow">Local explanation</p>
          <h2 id="risk-summary-title">Risk summary</h2>
        </div>
        <span
          className={`risk-badge risk-badge--${explanation.risk_band}`}
        >
          {explanation.risk_band}
        </span>
      </div>
      <div className="metric-grid">
        <div>
          <span className="metric__label">
            Prediction
          </span>
          <strong>
            {explanation.prediction
              ? "Fraud"
              : "Legitimate"}
          </strong>
        </div>
        <div>
          <span className="metric__label">
            Fraud probability
          </span>
          <strong>
            {formatProbability(
              explanation.fraud_probability,
            )}
          </strong>
        </div>
        <div>
          <span className="metric__label">
            Base value
          </span>
          <strong>
            {Number(explanation.base_value).toFixed(4)}
          </strong>
        </div>
      </div>
      <p className="summary-copy">
        {explanation.summary}
      </p>
    </section>
  );
}
