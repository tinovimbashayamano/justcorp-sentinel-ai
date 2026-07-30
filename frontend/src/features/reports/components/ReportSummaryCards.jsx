export default function ReportSummaryCards({ summary }) {
  const cards = [
    ["Total reports", summary.total_reports],
    ["Completed", summary.completed_reports],
    ["Failed", summary.failed_reports],
    ["Scheduled", summary.scheduled_reports],
    ["Downloads this month", summary.downloads_this_month],
    ["Storage used", `${summary.storage_used_mb ?? 0} MB`],
  ];

  return (
    <section className="report-summary" aria-label="Report summary">
      {cards.map(([label, value]) => (
        <article key={label}>
          <span>{label}</span>
          <strong>{value}</strong>
        </article>
      ))}
    </section>
  );
}
