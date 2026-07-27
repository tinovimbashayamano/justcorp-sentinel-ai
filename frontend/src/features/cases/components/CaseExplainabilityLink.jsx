import { Link } from "react-router";

export default function CaseExplainabilityLink({
  caseRecord,
  score,
}) {
  if (!caseRecord || !score) return null;

  const state = {
    caseId: caseRecord.id,
    transactionId: score.transaction_id,
    fraudScoreRecordId: score.id,
  };

  return (
    <section className="case-panel">
      <div className="case-panel__header">
        <div>
          <p className="case-eyebrow">Model evidence</p>
          <h2>Explainability workspace</h2>
        </div>
      </div>
      <p className="case-muted">
        Open the SHAP investigation workspace for the
        selected transaction.
      </p>
      <Link
        className="case-primary-link"
        to="/fraud/explainability"
        state={state}
      >
        Open transaction explanation
      </Link>
    </section>
  );
}
