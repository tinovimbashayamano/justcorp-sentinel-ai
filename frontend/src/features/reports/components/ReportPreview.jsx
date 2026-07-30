import {
  formatBytes,
  formatDateTime,
  reportTypeLabel,
  statusClass,
} from "../domain/reports";

export default function ReportPreview({ report, onDownload }) {
  if (!report) {
    return (
      <section className="report-panel report-preview-empty">
        Select a report to inspect its metadata and download availability.
      </section>
    );
  }

  return (
    <section className="report-panel">
      <header className="report-panel-header">
        <div><p>Preview</p><h2>{report.title}</h2></div>
        <span className={statusClass(report.status)}>{report.status}</span>
      </header>

      <dl className="report-metadata">
        <div><dt>Report ID</dt><dd>{report.id}</dd></div>
        <div><dt>Type</dt><dd>{reportTypeLabel(report.report_type)}</dd></div>
        <div><dt>Format</dt><dd>{String(report.output_format ?? "").toUpperCase()}</dd></div>
        <div><dt>Creator</dt><dd>{report.created_by}</dd></div>
        <div><dt>Created</dt><dd>{formatDateTime(report.created_at)}</dd></div>
        <div><dt>Expires</dt><dd>{formatDateTime(report.expires_at)}</dd></div>
        <div><dt>File size</dt><dd>{formatBytes(report.file_size_bytes)}</dd></div>
        <div><dt>Downloads</dt><dd>{report.download_count ?? 0}</dd></div>
      </dl>

      {report.description ? <p>{report.description}</p> : null}

      <button
        type="button"
        disabled={report.status !== "Completed"}
        onClick={() =>
          onDownload(
            report.id,
            report.file_name ??
              `${report.title}.${String(report.output_format).toLowerCase()}`
          )
        }
      >
        Download report
      </button>
    </section>
  );
}
