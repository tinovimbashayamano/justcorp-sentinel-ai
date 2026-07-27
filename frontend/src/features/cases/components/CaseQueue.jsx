function formatDate(value) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

export default function CaseQueue({
  cases,
  selectedCaseId,
  onSelect,
  loading,
}) {
  return (
    <section className="case-panel case-queue">
      <div className="case-panel__header">
        <div>
          <p className="case-eyebrow">Review queue</p>
          <h2>Fraud cases</h2>
        </div>
        <span>{cases.length}</span>
      </div>

      {loading ? <p>Loading cases…</p> : null}
      {!loading && cases.length === 0 ? (
        <p className="case-muted">
          No fraud cases are available.
        </p>
      ) : null}

      <div className="case-list">
        {cases.map((item) => (
          <button
            type="button"
            key={item.id}
            className={`case-list__item ${
              selectedCaseId === item.id
                ? "case-list__item--active"
                : ""
            }`}
            onClick={() => onSelect(item.id)}
          >
            <span>
              <strong>Case #{item.id}</strong>
              <small>
                Score record #
                {item.fraud_score_record_id}
              </small>
            </span>
            <span>
              <em>
                {item.case_status.replaceAll("_", " ")}
              </em>
              <small>{formatDate(item.updated_at)}</small>
            </span>
          </button>
        ))}
      </div>
    </section>
  );
}
