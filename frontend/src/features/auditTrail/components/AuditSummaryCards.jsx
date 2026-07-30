export default function AuditSummaryCards({ summary }) {
  const cards = [
    ["Total events", summary.total_events], ["Security events", summary.security_events],
    ["Failed authentication", summary.failed_authentication_attempts],
    ["Administrative changes", summary.administrative_changes],
    ["High-risk actions", summary.high_risk_actions], ["Exports and downloads", summary.export_download_events],
    ["Unique users", summary.unique_users], ["Last 24 hours", summary.events_last_24_hours],
  ];
  return <section className="audit-summary" aria-label="Audit summary">
    {cards.map(([label, value]) => <article key={label}><span>{label}</span><strong>{value}</strong></article>)}
  </section>;
}
