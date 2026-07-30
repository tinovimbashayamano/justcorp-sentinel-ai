export default function ReportTemplates({ templates }) {
  return (
    <section className="report-panel">
      <header className="report-panel-header">
        <div><p>Standardization</p><h2>Report templates</h2></div>
      </header>

      <div className="template-grid">
        {templates.map((template) => (
          <article key={template.id}>
            <strong>{template.name}</strong>
            <span>{template.description}</span>
            <small>{template.report_type}</small>
            <small>Version {template.version}</small>
          </article>
        ))}
      </div>

      {templates.length === 0 ? (
        <p className="empty-state">No report templates are available.</p>
      ) : null}
    </section>
  );
}
