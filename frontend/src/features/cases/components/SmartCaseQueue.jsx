function formatProbability(score) {
  const probability = Number(
    score?.fraud_probability ??
      score?.probability ??
      score?.fraud_score ??
      0
  );

  return new Intl.NumberFormat("en-US", {
    style: "percent",
    maximumFractionDigits: 1,
  }).format(probability);
}

export default function SmartCaseQueue({
  cases,
  scores,
  selectedCaseId,
  loading,
  onSelect,
}) {
  const scoresById = new Map(
    scores.map((score) => [score.id, score])
  );

  return (
    <section className="smart-case-queue">
      <div className="smart-case-queue__header">
        <div>
          <p className="case-eyebrow">Investigation queue</p>
          <h2>Cases</h2>
        </div>
        <span>{cases.length} shown</span>
      </div>

      {loading ? (
        <p>Loading cases…</p>
      ) : cases.length === 0 ? (
        <p className="case-muted">
          No cases match the current filters.
        </p>
      ) : (
        <div className="smart-case-list">
          {cases.map((caseRecord) => {
            const score = scoresById.get(
              caseRecord.fraud_score_record_id
            );
            const active = caseRecord.id === selectedCaseId;

            return (
              <button
                className={`smart-case-item ${
                  active ? "smart-case-item--active" : ""
                }`}
                type="button"
                key={caseRecord.id}
                onClick={() => onSelect(caseRecord.id)}
              >
                <div>
                  <strong>
                    {score?.transaction_id ||
                      `Case ${caseRecord.id}`}
                  </strong>
                  <span>
                    {caseRecord.case_status.replaceAll("_", " ")}
                  </span>
                </div>
                <div className="smart-case-item__metrics">
                  <span className={`case-risk case-risk--${score?.risk_band || "unknown"}`}>
                    {score?.risk_band || "unknown"}
                  </span>
                  <strong>{formatProbability(score)}</strong>
                </div>
              </button>
            );
          })}
        </div>
      )}
    </section>
  );
}
