import { useEffect, useState } from "react";
import { useReportingDashboard } from "../hooks/useReportingDashboard";
import "../styles/reporting.css";

const money = (value) =>
  new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value || 0);

const percent = (value) =>
  new Intl.NumberFormat("en-US", {
    style: "percent",
    maximumFractionDigits: 1,
  }).format(value || 0);

export default function ReportingDashboardPage() {
  const report = useReportingDashboard();
  const [filters, setFilters] = useState(report.filters);
  const [schedule, setSchedule] = useState({
    name: "",
    frequency: "weekly",
    report_type: "executive",
  });

  useEffect(() => {
    report.loadDashboard().catch(() => undefined);
  }, [report.loadDashboard]);

  const cards = [
    ["Transactions reviewed", report.summary.transactionsReviewed],
    ["Fraud cases", report.summary.fraudCases],
    ["Fraud prevented", money(report.summary.fraudPrevented)],
    ["Open investigations", report.summary.openInvestigations],
    ["High-risk alerts", report.summary.highRiskAlerts],
    ["Average review", `${report.summary.averageReviewHours.toFixed(1)} hrs`],
    ["Precision", percent(report.summary.precision)],
    ["Recall", percent(report.summary.recall)],
  ];

  const trendMax = Math.max(...report.trends.map((item) => item.alerts), 1);
  const riskTotal = report.riskDistribution.reduce(
    (sum, item) => sum + item.count,
    0
  );

  return (
    <main className="reporting-page">
      <header className="reporting-header">
        <p>JustCorp Sentinel AI</p>
        <h1>Executive reporting and compliance</h1>
        <span>
          Monitor fraud exposure, operations, model performance and governance.
        </span>
      </header>

      <section className="reporting-filters">
        <input
          type="date"
          value={filters.date_from}
          onChange={(event) =>
            setFilters({ ...filters, date_from: event.target.value })
          }
        />
        <input
          type="date"
          value={filters.date_to}
          onChange={(event) =>
            setFilters({ ...filters, date_to: event.target.value })
          }
        />
        <select
          value={filters.department}
          onChange={(event) =>
            setFilters({ ...filters, department: event.target.value })
          }
        >
          <option value="all">All departments</option>
          <option value="fraud_operations">Fraud Operations</option>
          <option value="risk_analytics">Risk Analytics</option>
          <option value="compliance">Compliance</option>
        </select>
        <select
          value={filters.risk_level}
          onChange={(event) =>
            setFilters({ ...filters, risk_level: event.target.value })
          }
        >
          <option value="all">All risk levels</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
        <button onClick={() => report.loadDashboard(filters)}>
          Apply filters
        </button>
        <button
          disabled={report.exporting}
          onClick={() => report.downloadReport("executive_report", "pdf")}
        >
          Export PDF
        </button>
      </section>

      {report.error ? (
        <div className="reporting-error" role="alert">
          {report.error.message}
        </div>
      ) : null}

      {report.loading ? (
        <section className="reporting-panel">Loading reporting data...</section>
      ) : (
        <>
          <div className="reporting-summary">
            {cards.map(([label, value]) => (
              <article key={label}>
                <span>{label}</span>
                <strong>{value}</strong>
              </article>
            ))}
          </div>

          <div className="reporting-grid">
            <section className="reporting-panel">
              <header>
                <p>Time series</p>
                <h2>Fraud and alert trends</h2>
              </header>
              <div className="reporting-bars">
                {report.trends.length ? (
                  report.trends.map((item) => (
                    <article key={item.date}>
                      <div
                        className="reporting-bar"
                        style={{
                          height: `${Math.max(
                            (item.alerts / trendMax) * 180,
                            4
                          )}px`,
                        }}
                        title={`${item.alerts} alerts`}
                      />
                      <small>{item.date}</small>
                    </article>
                  ))
                ) : (
                  <p>No trend data is available.</p>
                )}
              </div>
            </section>

            <section className="reporting-panel">
              <header>
                <p>Exposure</p>
                <h2>Risk distribution</h2>
              </header>
              <div className="reporting-risk">
                {report.riskDistribution.map((item) => {
                  const value = riskTotal
                    ? Math.round((item.count / riskTotal) * 100)
                    : 0;
                  return (
                    <article key={item.riskLevel}>
                      <strong>{item.riskLevel}</strong>
                      <div className="reporting-progress">
                        <span style={{ width: `${value}%` }} />
                      </div>
                      <small>
                        {item.count} ({value}%)
                      </small>
                    </article>
                  );
                })}
              </div>
            </section>
          </div>

          <section className="reporting-panel">
            <header>
              <p>Operations</p>
              <h2>Case performance</h2>
            </header>
            <div className="reporting-scroll">
              <table>
                <thead>
                  <tr>
                    <th>Case</th>
                    <th>Risk</th>
                    <th>Analyst</th>
                    <th>Status</th>
                    <th>Opened</th>
                    <th>Duration</th>
                    <th>Decision</th>
                    <th>Fraud amount</th>
                  </tr>
                </thead>
                <tbody>
                  {report.cases.map((item) => (
                    <tr key={item.id}>
                      <td>{item.case_id ?? item.id}</td>
                      <td>{item.risk_level ?? "-"}</td>
                      <td>{item.analyst_name ?? "Unassigned"}</td>
                      <td>{item.status ?? "-"}</td>
                      <td>
                        {item.opened_at
                          ? new Date(item.opened_at).toLocaleDateString()
                          : "-"}
                      </td>
                      <td>{item.duration_hours ?? "-"} hrs</td>
                      <td>{item.decision ?? "Pending"}</td>
                      <td>{money(item.fraud_amount)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section className="reporting-panel">
            <header>
              <p>Productivity</p>
              <h2>Analyst performance</h2>
            </header>
            <div className="reporting-scroll">
              <table>
                <thead>
                  <tr>
                    <th>Analyst</th>
                    <th>Assigned</th>
                    <th>Completed</th>
                    <th>Average review</th>
                    <th>Escalation</th>
                    <th>SLA compliance</th>
                  </tr>
                </thead>
                <tbody>
                  {report.analysts.map((item) => (
                    <tr key={item.id}>
                      <td>{item.name ?? item.full_name}</td>
                      <td>{item.cases_assigned ?? 0}</td>
                      <td>{item.cases_completed ?? 0}</td>
                      <td>{item.average_review_hours ?? 0} hrs</td>
                      <td>{percent(item.escalation_rate ?? 0)}</td>
                      <td>{percent(item.sla_compliance ?? 0)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <div className="reporting-grid">
            <section className="reporting-panel">
              <header>
                <p>Governance</p>
                <h2>Model performance</h2>
              </header>
              <div className="reporting-metrics">
                {[
                  ["Version", report.modelPerformance.model_version ?? "-"],
                  ["ROC-AUC", report.modelPerformance.roc_auc ?? "-"],
                  ["PR-AUC", report.modelPerformance.pr_auc ?? "-"],
                  ["Precision", report.modelPerformance.precision ?? "-"],
                  ["Recall", report.modelPerformance.recall ?? "-"],
                  ["F1-score", report.modelPerformance.f1_score ?? "-"],
                  ["False-positive rate", report.modelPerformance.false_positive_rate ?? "-"],
                  ["Drift status", report.modelPerformance.drift_status ?? "Unknown"],
                ].map(([label, value]) => (
                  <article key={label}>
                    <span>{label}</span>
                    <strong>{String(value)}</strong>
                  </article>
                ))}
              </div>
            </section>

            <section className="reporting-panel">
              <header>
                <p>Compliance</p>
                <h2>Control status</h2>
              </header>
              <div className="reporting-risk">
                {report.compliance.map((item) => (
                  <article key={item.label}>
                    <strong>{item.label}</strong>
                    <div className="reporting-progress">
                      <span style={{ width: `${item.value}%` }} />
                    </div>
                    <small>{item.value}% - {item.status}</small>
                  </article>
                ))}
              </div>
            </section>
          </div>

          <section className="reporting-panel">
            <header>
              <p>Automation</p>
              <h2>Scheduled reports</h2>
            </header>
            <form
              className="reporting-schedule"
              onSubmit={async (event) => {
                event.preventDefault();
                const created = await report.addSchedule(schedule);
                if (created) {
                  setSchedule({
                    name: "",
                    frequency: "weekly",
                    report_type: "executive",
                  });
                }
              }}
            >
              <input
                placeholder="Schedule name"
                value={schedule.name}
                onChange={(event) =>
                  setSchedule({ ...schedule, name: event.target.value })
                }
              />
              <select
                value={schedule.frequency}
                onChange={(event) =>
                  setSchedule({ ...schedule, frequency: event.target.value })
                }
              >
                <option value="daily">Daily</option>
                <option value="weekly">Weekly</option>
                <option value="monthly">Monthly</option>
                <option value="quarterly">Quarterly</option>
              </select>
              <select
                value={schedule.report_type}
                onChange={(event) =>
                  setSchedule({ ...schedule, report_type: event.target.value })
                }
              >
                <option value="executive">Executive</option>
                <option value="compliance">Compliance</option>
                <option value="model_governance">Model governance</option>
              </select>
              <button disabled={!schedule.name.trim()}>Add schedule</button>
            </form>

            <div className="reporting-cards">
              {report.schedules.map((item) => (
                <article key={item.id}>
                  <div>
                    <strong>{item.name}</strong>
                    <span>{item.report_type} - {item.frequency}</span>
                  </div>
                  <button onClick={() => report.removeSchedule(item.id)}>
                    Delete
                  </button>
                </article>
              ))}
            </div>
          </section>

          <section className="reporting-panel">
            <header>
              <p>Evidence</p>
              <h2>Audit evidence</h2>
            </header>
            <strong>{report.auditEvidence.length} records available</strong>
          </section>
        </>
      )}
    </main>
  );
}
