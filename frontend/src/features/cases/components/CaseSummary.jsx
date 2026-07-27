function percentage(value) {
  return new Intl.NumberFormat("en-US", {
    style: "percent",
    maximumFractionDigits: 2,
  }).format(Number(value || 0));
}

export default function CaseSummary({
  caseRecord,
  score,
}) {
  if (!caseRecord) {
    return (
      <section className="case-panel case-empty">
        Select a case from the review queue.
      </section>
    );
  }

  const decision =
    caseRecord.analyst_decision || "pending";

  return (
    <section className="case-panel">
      <div className="case-panel__header">
        <div>
          <p className="case-eyebrow">
            Investigation overview
          </p>
          <h2>Case #{caseRecord.id}</h2>
        </div>
        <span
          className={`case-status case-status--${caseRecord.case_status}`}
        >
          {caseRecord.case_status.replaceAll("_", " ")}
        </span>
      </div>

      <div className="case-metrics">
        <div>
          <span>Decision</span>
          <strong>
            {decision.replaceAll("_", " ")}
          </strong>
        </div>
        <div>
          <span>Fraud probability</span>
          <strong>
            {score
              ? percentage(score.fraud_probability)
              : "—"}
          </strong>
        </div>
        <div>
          <span>Risk band</span>
          <strong>{score?.risk_band || "—"}</strong>
        </div>
        <div>
          <span>Reviewed by</span>
          <strong>
            {caseRecord.reviewed_by || "Unassigned"}
          </strong>
        </div>
      </div>

      <dl className="case-details">
        <div>
          <dt>Fraud score record</dt>
          <dd>{caseRecord.fraud_score_record_id}</dd>
        </div>
        <div>
          <dt>Transaction</dt>
          <dd>{score?.transaction_id || "—"}</dd>
        </div>
        <div>
          <dt>Model</dt>
          <dd>{score?.model_name || "—"}</dd>
        </div>
        <div>
          <dt>Threshold</dt>
          <dd>{score?.fraud_threshold ?? "—"}</dd>
        </div>
      </dl>
    </section>
  );
}
