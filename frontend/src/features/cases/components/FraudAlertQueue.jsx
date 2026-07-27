import { findCaseForScore } from "../domain/caseQueue";

function probability(score) {
  return Number(
    score.fraud_probability ??
      score.probability ??
      score.fraud_score ??
      0
  );
}

export default function FraudAlertQueue({
  scores,
  cases,
  onInvestigate,
  loading,
}) {
  const highRisk = [...scores]
    .filter(
      (score) =>
        score.prediction === 1 ||
        score.is_fraud === true ||
        probability(score) >= 0.5
    )
    .sort((a, b) => probability(b) - probability(a))
    .slice(0, 20);

  return (
    <section className="fraud-alert-panel">
      <div className="smart-case-queue__header">
        <div>
          <p className="case-eyebrow">Fraud alerts</p>
          <h2>Alert-to-case workflow</h2>
        </div>
        <span>{highRisk.length} alerts</span>
      </div>

      {highRisk.length === 0 ? (
        <p className="case-muted">
          No fraud alerts are currently available.
        </p>
      ) : (
        <div className="fraud-alert-list">
          {highRisk.map((score) => {
            const existing = findCaseForScore(cases, score.id);

            return (
              <article className="fraud-alert-item" key={score.id}>
                <div>
                  <strong>
                    {score.transaction_id || `Score ${score.id}`}
                  </strong>
                  <span>
                    {score.merchant_name ||
                      score.merchant ||
                      score.customer_id ||
                      "No merchant or customer supplied"}
                  </span>
                </div>

                <div className="fraud-alert-item__actions">
                  <span className={`case-risk case-risk--${score.risk_band || "unknown"}`}>
                    {score.risk_band || "unknown"}
                  </span>
                  <strong>
                    {new Intl.NumberFormat("en-US", {
                      style: "percent",
                      maximumFractionDigits: 1,
                    }).format(probability(score))}
                  </strong>
                  <button
                    type="button"
                    disabled={loading}
                    onClick={() => onInvestigate(score.id)}
                  >
                    {existing ? "Open case" : "Investigate"}
                  </button>
                </div>
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}
