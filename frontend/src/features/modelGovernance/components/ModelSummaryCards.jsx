export default function ModelSummaryCards({ summary }) {
  const cards = [
    ["Registered models", summary.registered_models],
    ["Production models", summary.production_models],
    ["Pending approvals", summary.pending_approvals],
    ["Models with drift", summary.models_with_drift],
    ["Failed training runs", summary.failed_training_runs],
    ["Active experiments", summary.active_experiments],
  ];

  return (
    <section className="governance-summary" aria-label="Model summary">
      {cards.map(([label, value]) => (
        <article key={label}>
          <span>{label}</span>
          <strong>{value ?? "Not reported"}</strong>
        </article>
      ))}
    </section>
  );
}
