import { useEffect, useState } from "react";
import { useReportExports } from "../hooks/useReportExports";
import ReportSummaryCards from "../components/ReportSummaryCards";
import GenerateReportForm from "../components/GenerateReportForm";
import ReportHistoryTable from "../components/ReportHistoryTable";
import ReportPreview from "../components/ReportPreview";
import ReportTemplates from "../components/ReportTemplates";
import ScheduledReports from "../components/ScheduledReports";
import "../styles/reports.css";

const TABS = ["Dashboard", "Generate", "History", "Templates", "Scheduled", "Downloads"];

export default function ReportExportDashboard() {
  const reports = useReportExports();
  const [tab, setTab] = useState("Dashboard");

  useEffect(() => {
    reports.load().catch(() => undefined);
  }, [reports.load]);

  return (
    <main className="report-export-page">
      <header className="report-hero">
        <div>
          <p>JustCorp Sentinel AI</p>
          <h1>Enterprise report generation</h1>
          <span>Generate, schedule, govern and download PDF, Excel and CSV reports.</span>
        </div>
        <div className="report-hero-stat">
          <span>Completed reports</span>
          <strong>{reports.summary.completed_reports}</strong>
        </div>
      </header>

      <ReportSummaryCards summary={reports.summary} />

      <nav className="report-tabs" aria-label="Report sections">
        {TABS.map((item) => (
          <button type="button" key={item}
            className={tab === item ? "active" : ""}
            onClick={() => setTab(item)}>
            {item}
          </button>
        ))}
      </nav>

      {reports.error ? (
        <div className="report-error" role="alert">{reports.error.message}</div>
      ) : null}

      {reports.loading ? (
        <section className="report-panel">Loading report center…</section>
      ) : (
        <>
          {tab === "Dashboard" && (
            <>
              <div className="report-two-column">
                <ReportPreview report={reports.selectedReport} onDownload={reports.download} />
                <ReportTemplates templates={reports.templates.slice(0, 4)} />
              </div>
              <ReportHistoryTable
                reports={reports.visibleReports.slice(0, 10)}
                filters={reports.filters}
                setFilters={reports.setFilters}
                onSelect={reports.selectReport}
                onDownload={reports.download}
                onDelete={reports.remove}
              />
            </>
          )}

          {tab === "Generate" && (
            <GenerateReportForm
              onGenerate={async (payload) => {
                await reports.generate(payload);
                setTab("History");
              }}
              actionLoading={reports.actionLoading}
            />
          )}

          {tab === "History" && (
            <ReportHistoryTable
              reports={reports.visibleReports}
              filters={reports.filters}
              setFilters={reports.setFilters}
              onSelect={reports.selectReport}
              onDownload={reports.download}
              onDelete={reports.remove}
            />
          )}

          {tab === "Templates" && <ReportTemplates templates={reports.templates} />}

          {tab === "Scheduled" && (
            <ScheduledReports
              schedules={reports.scheduled}
              onCreate={reports.schedule}
              onCancel={reports.cancelSchedule}
              actionLoading={reports.actionLoading}
            />
          )}

          {tab === "Downloads" && (
            <ReportHistoryTable
              reports={reports.visibleReports.filter((report) => report.status === "Completed")}
              filters={reports.filters}
              setFilters={reports.setFilters}
              onSelect={reports.selectReport}
              onDownload={reports.download}
              onDelete={reports.remove}
            />
          )}
        </>
      )}

      {reports.actionLoading ? (
        <div className="report-progress">Processing report request…</div>
      ) : null}
    </main>
  );
}
