import {
  formatBytes,
  formatDateTime,
  reportTypeLabel,
  statusClass,
} from "../domain/reports";

export default function ReportHistoryTable({
  reports,
  filters,
  setFilters,
  onSelect,
  onDownload,
  onDelete,
}) {
  return (
    <section className="report-panel">
      <header className="report-panel-header">
        <div><p>Archive</p><h2>Report history</h2></div>
        <div className="report-filter-row">
          <input aria-label="Search reports" placeholder="Search reports"
            value={filters.search}
            onChange={(event) => setFilters((current) => ({ ...current, search: event.target.value }))} />
          <select aria-label="Filter report status" value={filters.status}
            onChange={(event) => setFilters((current) => ({ ...current, status: event.target.value }))}>
            <option>All</option><option>Queued</option><option>Generating</option>
            <option>Completed</option><option>Failed</option><option>Expired</option>
          </select>
          <select aria-label="Filter report format" value={filters.format}
            onChange={(event) => setFilters((current) => ({ ...current, format: event.target.value }))}>
            <option>All</option><option>PDF</option><option>XLSX</option><option>CSV</option>
          </select>
        </div>
      </header>

      <div className="report-table-scroll">
        <table>
          <thead>
            <tr><th>Report</th><th>Type</th><th>Format</th><th>Status</th>
              <th>Created by</th><th>Created</th><th>Size</th><th>Downloads</th><th>Actions</th></tr>
          </thead>
          <tbody>
            {reports.map((report) => (
              <tr key={report.id} onClick={() => onSelect(report)}>
                <td>{report.title}</td>
                <td>{reportTypeLabel(report.report_type)}</td>
                <td>{String(report.output_format ?? "").toUpperCase()}</td>
                <td><span className={statusClass(report.status)}>{report.status}</span></td>
                <td>{report.created_by}</td>
                <td>{formatDateTime(report.created_at)}</td>
                <td>{formatBytes(report.file_size_bytes)}</td>
                <td>{report.download_count ?? 0}</td>
                <td>
                  <div className="table-actions">
                    <button type="button" disabled={report.status !== "Completed"}
                      onClick={(event) => {
                        event.stopPropagation();
                        onDownload(report.id, report.file_name ??
                          `${report.title}.${String(report.output_format).toLowerCase()}`);
                      }}>Download</button>
                    <button type="button" className="danger"
                      onClick={(event) => {
                        event.stopPropagation();
                        onDelete(report.id);
                      }}>Delete</button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {reports.length === 0 ? <p className="empty-state">No reports match the selected filters.</p> : null}
    </section>
  );
}
