import { useEffect, useState } from "react";
import { useOperationsDashboard } from "../hooks/useOperationsDashboard";
import { formatMetric } from "../domain/operations";
import "../styles/operations.css";

const percent = (value) =>
  value == null
    ? "Not reported"
    : new Intl.NumberFormat("en-US", {
        style: "percent",
        maximumFractionDigits: 1,
      }).format(Number(value || 0));

const emptyIncident = {
  summary: "",
  affected_service: "FastAPI backend",
  severity: "medium",
};

export default function OperationsDashboardPage() {
  const operations = useOperationsDashboard();
  const [filters, setFilters] = useState(operations.filters);
  const [thresholds, setThresholds] = useState({});
  const [incident, setIncident] = useState(emptyIncident);

  useEffect(() => {
    operations.loadDashboard().catch(() => undefined);
  }, [operations.loadDashboard]);

  useEffect(() => {
    setThresholds(operations.thresholds || {});
  }, [operations.thresholds]);

  const cards = [
    ["System status", operations.summary.status],
    ["API uptime", percent(operations.summary.uptime)],
    ["Error rate", percent(operations.summary.errorRate)],
    [
      "Average response",
      formatMetric(operations.summary.averageLatency, " ms"),
    ],
    ["Throughput", formatMetric(operations.summary.throughput, "/min")],
    ["Active users", formatMetric(operations.summary.activeUsers)],
    [
      "DB connections",
      formatMetric(operations.summary.databaseConnections),
    ],
    ["Queue backlog", formatMetric(operations.summary.queueBacklog)],
  ];

  const submitIncident = async (event) => {
    event.preventDefault();
    if (!incident.summary.trim()) return;
    await operations.addIncident(incident);
    setIncident(emptyIncident);
  };

  const submitThresholds = async (event) => {
    event.preventDefault();
    await operations.saveThresholds(thresholds);
  };

  return (
    <main className="operations-page">
      <header className="operations-header">
        <p>JustCorp Sentinel AI</p>
        <h1>System health and operations</h1>
        <span>
          Monitor availability, performance, deployments, incidents and logs.
        </span>
      </header>

      <section className="operations-filters" aria-label="Dashboard filters">
        <label>
          Environment
          <select
            value={filters.environment}
            onChange={(event) =>
              setFilters({ ...filters, environment: event.target.value })
            }
          >
            <option value="all">All environments</option>
            <option value="development">Development</option>
            <option value="staging">Staging</option>
            <option value="production">Production</option>
          </select>
        </label>
        <label>
          Time range
          <select
            value={filters.time_range}
            onChange={(event) =>
              setFilters({ ...filters, time_range: event.target.value })
            }
          >
            <option value="1h">Last hour</option>
            <option value="24h">Last 24 hours</option>
            <option value="7d">Last 7 days</option>
            <option value="30d">Last 30 days</option>
          </select>
        </label>
        <button
          type="button"
          onClick={() => operations.loadDashboard(filters)}
          disabled={operations.loading}
        >
          {operations.loading ? "Refreshing..." : "Refresh"}
        </button>
      </section>

      {operations.error ? (
        <div className="operations-error" role="alert">
          {operations.error.message}
        </div>
      ) : null}

      {operations.loading ? (
        <section className="operations-panel">Loading operations data...</section>
      ) : (
        <>
          <div className="operations-summary">
            {cards.map(([label, value]) => (
              <article key={label}>
                <span>{label}</span>
                <strong>{value}</strong>
              </article>
            ))}
          </div>

          <div className="operations-grid">
            <section className="operations-panel">
              <header>
                <p>Availability</p>
                <h2>Service status</h2>
              </header>
              <div className="operations-service-list">
                {operations.services.length ? (
                  operations.services.map((service) => (
                    <article key={service.id}>
                      <div>
                        <strong>{service.name}</strong>
                        <span>
                          {service.version} / {service.environment}
                        </span>
                      </div>
                      <span className={`status-${service.status}`}>
                        {service.status}
                      </span>
                      <small>{service.responseTime} ms</small>
                    </article>
                  ))
                ) : (
                  <p className="operations-empty">
                    No service checks are available.
                  </p>
                )}
              </div>
            </section>

            <section className="operations-panel">
              <header>
                <p>Performance</p>
                <h2>API performance</h2>
              </header>
              <div className="operations-metrics">
                {[
                  [
                    "Requests",
                    operations.apiPerformance.total_requests ?? 0,
                  ],
                  [
                    "P50 latency",
                    `${operations.apiPerformance.p50_latency_ms ?? 0} ms`,
                  ],
                  [
                    "P95 latency",
                    `${operations.apiPerformance.p95_latency_ms ?? 0} ms`,
                  ],
                  [
                    "P99 latency",
                    `${operations.apiPerformance.p99_latency_ms ?? 0} ms`,
                  ],
                  [
                    "Success rate",
                    percent(operations.apiPerformance.success_rate ?? 0),
                  ],
                  [
                    "Server errors",
                    operations.apiPerformance.server_errors ?? 0,
                  ],
                ].map(([label, value]) => (
                  <article key={label}>
                    <span>{label}</span>
                    <strong>{value}</strong>
                  </article>
                ))}
              </div>
            </section>
          </div>

          <div className="operations-grid">
            <section className="operations-panel">
              <header>
                <p>Infrastructure</p>
                <h2>Resource usage</h2>
              </header>
              <div className="operations-resources">
                {operations.resources.map((item) => (
                  <article key={item.label}>
                    <strong>{item.label}</strong>
                    <div className="operations-progress">
                      <span
                        style={{
                          width: `${Math.min(item.value ?? 0, 100)}%`,
                        }}
                      />
                    </div>
                    <small>
                      {item.value == null ? "N/A" : `${item.value}%`}
                    </small>
                  </article>
                ))}
              </div>
              <p className="operations-note">
                Host CPU, memory and disk telemetry require a dedicated
                operations backend.
              </p>
            </section>

            <section className="operations-panel">
              <header>
                <p>Data layer</p>
                <h2>Database connectivity</h2>
              </header>
              <div className="operations-metrics">
                {[
                  ["Status", operations.database?.status || "unknown"],
                  [
                    "Response time",
                    formatMetric(
                      operations.database?.response_time_ms,
                      " ms",
                    ),
                  ],
                  [
                    "Connections",
                    formatMetric(operations.database?.connections),
                  ],
                  [
                    "Pool utilization",
                    operations.database?.pool_utilization == null
                      ? "Not reported"
                      : percent(operations.database.pool_utilization),
                  ],
                ].map(([label, value]) => (
                  <article key={label}>
                    <span>{label}</span>
                    <strong>{value}</strong>
                  </article>
                ))}
              </div>
            </section>
          </div>

          <section className="operations-panel">
            <header>
              <p>Automation</p>
              <h2>Background jobs</h2>
            </header>
            <div className="operations-scroll">
              <table>
                <thead>
                  <tr>
                    <th>Job</th>
                    <th>Type</th>
                    <th>Status</th>
                    <th>Started</th>
                    <th>Duration</th>
                    <th>Attempts</th>
                    <th>Next run</th>
                  </tr>
                </thead>
                <tbody>
                  {operations.jobs.length ? (
                    operations.jobs.map((job) => (
                      <tr key={job.id}>
                        <td>{job.name}</td>
                        <td>{job.job_type}</td>
                        <td>{job.status}</td>
                        <td>{job.started_at ?? "Not reported"}</td>
                        <td>
                          {job.duration_seconds == null
                            ? "Not reported"
                            : `${job.duration_seconds} sec`}
                        </td>
                        <td>{job.attempts ?? 0}</td>
                        <td>{job.next_run ?? "Not scheduled"}</td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="7">No background jobs were reported.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </section>

          <div className="operations-grid">
            <section className="operations-panel">
              <header>
                <p>Reliability</p>
                <h2>Recent incidents</h2>
              </header>
              <form
                className="operations-inline-form"
                onSubmit={submitIncident}
              >
                <input
                  aria-label="Incident summary"
                  placeholder="Incident summary"
                  value={incident.summary}
                  onChange={(event) =>
                    setIncident({
                      ...incident,
                      summary: event.target.value,
                    })
                  }
                />
                <select
                  aria-label="Incident severity"
                  value={incident.severity}
                  onChange={(event) =>
                    setIncident({
                      ...incident,
                      severity: event.target.value,
                    })
                  }
                >
                  <option value="critical">Critical</option>
                  <option value="high">High</option>
                  <option value="medium">Medium</option>
                  <option value="low">Low</option>
                  <option value="informational">Informational</option>
                </select>
                <button type="submit">Record incident</button>
              </form>
              <div className="operations-cards">
                {operations.incidents.length ? (
                  operations.incidents.map((item) => (
                    <article key={item.id}>
                      <div>
                        <strong>{item.summary}</strong>
                        <span>
                          {item.affected_service} / {item.status}
                        </span>
                      </div>
                      <span
                        className={`severity-${String(
                          item.severity,
                        ).toLowerCase()}`}
                      >
                        {item.severity}
                      </span>
                    </article>
                  ))
                ) : (
                  <p className="operations-empty">
                    No active incidents.
                  </p>
                )}
              </div>
            </section>

            <section className="operations-panel">
              <header>
                <p>Release</p>
                <h2>Deployment information</h2>
              </header>
              <div className="operations-metrics">
                {[
                  [
                    "Application",
                    operations.deployment.application_version ??
                      "Not reported",
                  ],
                  [
                    "Git commit",
                    operations.deployment.git_commit ?? "Not reported",
                  ],
                  [
                    "Branch",
                    operations.deployment.branch ?? "Not reported",
                  ],
                  [
                    "Environment",
                    operations.deployment.environment ?? "Not reported",
                  ],
                  [
                    "Backend",
                    operations.deployment.backend_version ?? "Not reported",
                  ],
                  [
                    "Frontend",
                    operations.deployment.frontend_version ?? "Not reported",
                  ],
                  [
                    "Model",
                    operations.deployment.model_version ?? "Not reported",
                  ],
                  [
                    "Migration",
                    operations.deployment.database_migration ??
                      "Not reported",
                  ],
                ].map(([label, value]) => (
                  <article key={label}>
                    <span>{label}</span>
                    <strong>{value}</strong>
                  </article>
                ))}
              </div>
            </section>
          </div>

          <section className="operations-panel">
            <header>
              <p>Diagnostics</p>
              <h2>Application logs</h2>
            </header>
            <div className="operations-log-filters">
              <select
                aria-label="Log level"
                value={filters.log_level}
                onChange={(event) =>
                  setFilters({ ...filters, log_level: event.target.value })
                }
              >
                <option value="all">All levels</option>
                <option value="debug">Debug</option>
                <option value="information">Information</option>
                <option value="warning">Warning</option>
                <option value="error">Error</option>
                <option value="critical">Critical</option>
              </select>
              <input
                placeholder="Search logs"
                value={filters.search}
                onChange={(event) =>
                  setFilters({ ...filters, search: event.target.value })
                }
              />
            </div>
            <div className="operations-scroll">
              <table>
                <thead>
                  <tr>
                    <th>Time</th>
                    <th>Level</th>
                    <th>Service</th>
                    <th>Message</th>
                    <th>Request ID</th>
                    <th>Endpoint</th>
                  </tr>
                </thead>
                <tbody>
                  {operations.logs.length ? (
                    operations.logs.map((log) => (
                      <tr key={log.id}>
                        <td>{log.timestamp}</td>
                        <td>{log.level}</td>
                        <td>{log.service}</td>
                        <td>{log.message}</td>
                        <td>{log.request_id ?? "Not reported"}</td>
                        <td>{log.endpoint ?? "Not reported"}</td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="6">No logs match the current filters.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </section>

          <section className="operations-panel">
            <header>
              <p>Configuration</p>
              <h2>Alert thresholds</h2>
            </header>
            <form
              className="operations-thresholds"
              onSubmit={submitThresholds}
            >
              {[
                ["Maximum API latency (ms)", "maximum_api_latency_ms"],
                ["Maximum error rate", "maximum_error_rate"],
                ["Minimum service uptime", "minimum_service_uptime"],
                ["Maximum CPU usage", "maximum_cpu_usage"],
                ["Maximum memory usage", "maximum_memory_usage"],
                [
                  "Maximum DB connections",
                  "maximum_database_connections",
                ],
                ["Maximum queue backlog", "maximum_queue_backlog"],
              ].map(([label, key]) => (
                <label key={key}>
                  {label}
                  <input
                    type="number"
                    step="any"
                    value={thresholds[key] ?? ""}
                    onChange={(event) =>
                      setThresholds({
                        ...thresholds,
                        [key]: Number(event.target.value),
                      })
                    }
                  />
                </label>
              ))}
              <button type="submit">Save thresholds</button>
            </form>
            <p className="operations-note">
              Incident and threshold changes are stored in this browser until
              persistent operations endpoints are available.
            </p>
          </section>
        </>
      )}
    </main>
  );
}
