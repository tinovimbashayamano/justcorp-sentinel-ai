export default function StatusBanner({ health, error }) {
  if (error) {
    return (
      <div
        className="status-banner status-banner--error"
        role="alert"
      >
        <strong>Explainability service unavailable.</strong>
        <span>{error.message}</span>
      </div>
    );
  }

  if (!health) {
    return (
      <div className="status-banner status-banner--neutral">
        Service status has not been checked.
      </div>
    );
  }

  const ready = health.status === "ready";
  return (
    <div
      className={`status-banner ${
        ready
          ? "status-banner--ready"
          : "status-banner--warning"
      }`}
    >
      <strong>
        {ready
          ? "Explainability ready"
          : "Service degraded"}
      </strong>
      <span>
        Local: {health.local_explainability} · Global:{" "}
        {health.global_explainability}
      </span>
    </div>
  );
}
