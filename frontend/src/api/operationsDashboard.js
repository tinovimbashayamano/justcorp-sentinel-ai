import { httpClient } from "./httpClient";

const SOURCE_CACHE_MS = 1200;
const INCIDENT_STORAGE_KEY = "sentinel_operations_incidents";
const THRESHOLD_STORAGE_KEY = "sentinel_operations_thresholds";
const DEFAULT_THRESHOLDS = {
  maximum_api_latency_ms: 1000,
  maximum_error_rate: 0.05,
  minimum_service_uptime: 0.99,
  maximum_cpu_usage: 85,
  maximum_memory_usage: 85,
  maximum_database_connections: 80,
  maximum_queue_backlog: 100,
  require_model_service: true,
};

let cachedKey = "";
let cachedAt = 0;
let cachedPromise = null;

function listItems(value) {
  if (Array.isArray(value)) return value;
  if (Array.isArray(value?.items)) return value.items;
  return [];
}

function readStoredValue(key, fallback) {
  try {
    return JSON.parse(window.localStorage.getItem(key) || "null") ?? fallback;
  } catch {
    return fallback;
  }
}

function writeStoredValue(key, value) {
  window.localStorage.setItem(key, JSON.stringify(value));
}

function createId(prefix) {
  if (globalThis.crypto?.randomUUID) {
    return globalThis.crypto.randomUUID();
  }
  return `${prefix}-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function healthStatus(value, fallback = "unknown") {
  const status = String(value || fallback).toLowerCase();
  if (["healthy", "ready", "active", "ok", "available"].includes(status)) {
    return "healthy";
  }
  if (["degraded", "warning", "partial"].includes(status)) {
    return "degraded";
  }
  if (["critical", "failed", "error", "unavailable", "offline"].includes(status)) {
    return "critical";
  }
  return fallback;
}

async function timedGet(path, config) {
  const startedAt = performance.now();
  try {
    const response = await httpClient.get(path, config);
    return {
      ok: true,
      data: response.data,
      latency: Math.max(0, Math.round(performance.now() - startedAt)),
      statusCode: response.status,
    };
  } catch (error) {
    return {
      ok: false,
      data: null,
      error,
      latency: Math.max(0, Math.round(performance.now() - startedAt)),
      statusCode: error.status || 0,
    };
  }
}

function percentile(values, percent) {
  if (!values.length) return 0;
  const ordered = [...values].sort((a, b) => a - b);
  const index = Math.min(
    ordered.length - 1,
    Math.ceil((percent / 100) * ordered.length) - 1,
  );
  return ordered[Math.max(0, index)];
}

function timeRangeMinutes(value) {
  return {
    "1h": 60,
    "24h": 24 * 60,
    "7d": 7 * 24 * 60,
    "30d": 30 * 24 * 60,
  }[value] || 24 * 60;
}

function currentEnvironment() {
  return import.meta.env.MODE || "development";
}

function buildServices(sources) {
  const environment = currentEnvironment();
  const analytics = sources.analytics.data || {};
  const explainability = sources.explainability.data || {};
  const fraud = sources.fraud.data || {};
  const insights = sources.insights.data || {};

  return [
    {
      id: "backend",
      name: "FastAPI backend",
      status: sources.backend.ok
        ? healthStatus(sources.backend.data?.status, "healthy")
        : "critical",
      response_time_ms: sources.backend.latency,
      uptime: sources.backend.ok ? 1 : 0,
      last_health_check: new Date().toISOString(),
      version: sources.backend.data?.version || "0.1.0",
      environment,
    },
    {
      id: "database",
      name: "Application database",
      status: sources.analytics.ok
        ? healthStatus(analytics.status, "healthy")
        : "unknown",
      response_time_ms: sources.analytics.latency,
      uptime: sources.analytics.ok ? 1 : 0,
      last_health_check: analytics.generated_at || new Date().toISOString(),
      version: "Managed by backend",
      environment,
    },
    {
      id: "fraud-model",
      name: "Fraud scoring model",
      status: sources.fraud.ok
        ? healthStatus(fraud.status, "healthy")
        : "unknown",
      response_time_ms: sources.fraud.latency,
      uptime: sources.fraud.ok ? 1 : 0,
      last_health_check: new Date().toISOString(),
      version: fraud.model_name || "Current model",
      environment,
    },
    {
      id: "explainability",
      name: "SHAP explainability",
      status: sources.explainability.ok
        ? healthStatus(explainability.status, "healthy")
        : "unknown",
      response_time_ms: sources.explainability.latency,
      uptime: sources.explainability.ok ? 1 : 0,
      last_health_check: new Date().toISOString(),
      version: explainability.model_name || fraud.model_name || "Current model",
      environment,
    },
    {
      id: "model-insights",
      name: "Model insights",
      status: sources.insights.ok
        ? healthStatus(insights.status, "healthy")
        : "unknown",
      response_time_ms: sources.insights.latency,
      uptime: sources.insights.ok ? 1 : 0,
      last_health_check: new Date().toISOString(),
      version: insights.model || "Current model",
      environment,
    },
    {
      id: "authentication",
      name: "Authentication service",
      status: sources.backend.ok ? "healthy" : "critical",
      response_time_ms: sources.backend.latency,
      uptime: sources.backend.ok ? 1 : 0,
      last_health_check: new Date().toISOString(),
      version: "Backend integrated",
      environment,
    },
    {
      id: "reporting",
      name: "Reporting service",
      status: sources.reports.ok ? "healthy" : "unknown",
      response_time_ms: sources.reports.latency,
      uptime: sources.reports.ok ? 1 : 0,
      last_health_check: new Date().toISOString(),
      version: "Backend integrated",
      environment,
    },
    {
      id: "frontend",
      name: "Frontend application",
      status: "healthy",
      response_time_ms: 0,
      uptime: 1,
      last_health_check: new Date().toISOString(),
      version: import.meta.env.VITE_APP_VERSION || "0.1.0",
      environment,
    },
  ];
}

function buildLogs(auditPayload) {
  return listItems(auditPayload).map((item) => {
    const failed = String(item.status || "").toLowerCase() !== "success";
    return {
      id: item.id,
      timestamp: item.created_at,
      level: failed ? "error" : "information",
      service: item.resource_type || "backend",
      message: item.action || "Application activity",
      request_id: item.details?.request_id || null,
      user_id: item.user_id || item.actor_username || null,
      endpoint: item.details?.endpoint || null,
    };
  });
}

function buildJobs(reportPayload) {
  return listItems(reportPayload).map((report) => ({
    id: `report-${report.id}`,
    name: report.title || `${report.report_type || "Case"} report`,
    job_type: "report_generation",
    status: report.status || "completed",
    started_at: report.created_at,
    completed_at: report.completed_at || report.updated_at || null,
    duration_seconds: report.duration_seconds ?? null,
    attempts: report.attempts ?? 1,
    failure_reason: report.error_message || null,
    next_run: null,
  }));
}

function buildIncidents(sources, services) {
  const stored = readStoredValue(INCIDENT_STORAGE_KEY, []);
  const generated = services
    .filter((service) => service.status === "critical")
    .map((service) => ({
      id: `health-${service.id}`,
      severity: "critical",
      affected_service: service.name,
      summary: `${service.name} health check failed`,
      status: "open",
      started_at: new Date().toISOString(),
      resolved_at: null,
      assigned_owner: null,
      resolution_notes: sources[service.id]?.error?.message || null,
      generated: true,
    }));
  return [...stored, ...generated];
}

function buildDashboard(sources, filters) {
  const services = buildServices(sources);
  const logs = buildLogs(sources.audit.data);
  const jobs = buildJobs(sources.reports.data);
  const latencies = Object.values(sources)
    .filter((source) => source && typeof source.latency === "number")
    .map((source) => source.latency);
  const sourceChecks = Object.values(sources).filter(
    (source) => source && typeof source.ok === "boolean",
  );
  const failedChecks = sourceChecks.filter((source) => !source.ok);
  const failedLogs = logs.filter((item) => item.level === "error");
  const actors = new Set(
    listItems(sources.audit.data)
      .map((item) => item.actor_username)
      .filter(Boolean),
  );
  const queueBacklog = jobs.filter((job) =>
    ["pending", "queued", "running", "retrying"].includes(
      String(job.status || "").toLowerCase(),
    ),
  ).length;
  const monitoredServices = services.filter(
    (service) => service.status !== "unknown",
  );
  const healthyServices = monitoredServices.filter(
    (service) => service.status === "healthy",
  ).length;
  const overallStatus = services.some((service) => service.status === "critical")
    ? "critical"
    : services.some((service) => service.status === "degraded")
      ? "degraded"
      : services.every((service) =>
            ["healthy", "unknown"].includes(service.status),
          )
        ? "healthy"
        : "unknown";
  const auditTotal = Number(sources.audit.data?.total ?? logs.length);
  const errorCount = failedLogs.length + failedChecks.length;
  const requestCount = Math.max(auditTotal, sourceChecks.length);

  return {
    summary: {
      status: overallStatus,
      api_uptime: monitoredServices.length
        ? healthyServices / monitoredServices.length
        : 0,
      average_response_time_ms: latencies.length
        ? latencies.reduce((sum, value) => sum + value, 0) / latencies.length
        : 0,
      requests_per_minute:
        requestCount / timeRangeMinutes(filters.time_range),
      error_rate: requestCount ? errorCount / requestCount : 0,
      active_users: actors.size,
      database_connections: null,
      queue_backlog: queueBacklog,
    },
    services,
    apiPerformance: {
      total_requests: requestCount,
      requests_per_minute:
        requestCount / timeRangeMinutes(filters.time_range),
      average_latency_ms: latencies.length
        ? latencies.reduce((sum, value) => sum + value, 0) / latencies.length
        : 0,
      p50_latency_ms: percentile(latencies, 50),
      p95_latency_ms: percentile(latencies, 95),
      p99_latency_ms: percentile(latencies, 99),
      success_rate: requestCount ? Math.max(0, 1 - errorCount / requestCount) : 0,
      client_errors: failedChecks.filter(
        (source) => source.statusCode >= 400 && source.statusCode < 500,
      ).length,
      server_errors:
        failedLogs.length +
        failedChecks.filter((source) => source.statusCode >= 500).length,
    },
    resources: {
      cpu_usage: null,
      memory_usage: null,
      disk_usage: null,
      database_storage_usage: null,
      connection_pool_usage: null,
      worker_utilization: null,
    },
    database: {
      status: services.find((service) => service.id === "database")?.status,
      response_time_ms: sources.analytics.latency,
      connections: null,
      pool_utilization: null,
      records_available: {
        transactions:
          sources.analytics.data?.transaction_records_available ?? null,
        fraud_scores: sources.analytics.data?.fraud_scores_available ?? null,
        cases: sources.analytics.data?.case_records_available ?? null,
        explainability:
          sources.analytics.data?.explainability_records_available ?? null,
      },
    },
    jobs,
    incidents: buildIncidents(sources, services),
    logs,
    deployment: {
      application_version: import.meta.env.VITE_APP_VERSION || "0.1.0",
      git_commit: import.meta.env.VITE_GIT_COMMIT || "Not exposed",
      branch: import.meta.env.VITE_GIT_BRANCH || "Not exposed",
      environment: currentEnvironment(),
      deployment_time: import.meta.env.VITE_DEPLOYED_AT || null,
      deployed_by: import.meta.env.VITE_DEPLOYED_BY || null,
      backend_version: sources.backend.data?.version || "0.1.0",
      frontend_version: import.meta.env.VITE_APP_VERSION || "0.1.0",
      model_version:
        sources.fraud.data?.model_name ||
        sources.insights.data?.model ||
        "Not reported",
      database_migration: "Not exposed",
    },
    thresholds: {
      ...DEFAULT_THRESHOLDS,
      ...readStoredValue(THRESHOLD_STORAGE_KEY, {}),
    },
  };
}

async function loadSources(filters = {}) {
  const key = JSON.stringify(filters);
  const now = Date.now();
  if (cachedPromise && cachedKey === key && now - cachedAt < SOURCE_CACHE_MS) {
    return cachedPromise;
  }

  cachedKey = key;
  cachedAt = now;
  cachedPromise = Promise.all([
    timedGet("/health"),
    timedGet("/api/v1/fraud/health"),
    timedGet("/api/v1/fraud/explainability/health"),
    timedGet("/api/v1/model-insights/health"),
    timedGet("/api/v1/analytics/health"),
    timedGet("/api/v1/audit-logs", { params: { limit: 200 } }),
    timedGet("/api/v1/reports", { params: { limit: 100 } }),
  ]).then(
    ([
      backend,
      fraud,
      explainability,
      insights,
      analytics,
      audit,
      reports,
    ]) => {
      if (!backend.ok) {
        throw backend.error || new Error("The backend health check failed.");
      }
      return buildDashboard(
        {
          backend,
          fraud,
          explainability,
          insights,
          analytics,
          audit,
          reports,
        },
        filters,
      );
    },
  );
  return cachedPromise;
}

function readIncidents() {
  return readStoredValue(INCIDENT_STORAGE_KEY, []);
}

function writeIncidents(items) {
  writeStoredValue(INCIDENT_STORAGE_KEY, items);
}

export const operationsApi = {
  summary: (params = {}) => loadSources(params).then((data) => data.summary),
  services: (params = {}) => loadSources(params).then((data) => data.services),
  apiPerformance: (params = {}) =>
    loadSources(params).then((data) => data.apiPerformance),
  resources: (params = {}) => loadSources(params).then((data) => data.resources),
  database: (params = {}) => loadSources(params).then((data) => data.database),
  jobs: (params = {}) => loadSources(params).then((data) => data.jobs),
  incidents: (params = {}) => loadSources(params).then((data) => data.incidents),
  logs: (params = {}) => loadSources(params).then((data) => data.logs),
  deployment: (params = {}) =>
    loadSources(params).then((data) => data.deployment),
  thresholds: () =>
    Promise.resolve({
      ...DEFAULT_THRESHOLDS,
      ...readStoredValue(THRESHOLD_STORAGE_KEY, {}),
    }),
  updateThresholds: (payload) => {
    const updated = {
      ...DEFAULT_THRESHOLDS,
      ...readStoredValue(THRESHOLD_STORAGE_KEY, {}),
      ...payload,
    };
    writeStoredValue(THRESHOLD_STORAGE_KEY, updated);
    return Promise.resolve(updated);
  },
  createIncident: (payload) => {
    const created = {
      id: createId("incident"),
      status: "open",
      started_at: new Date().toISOString(),
      ...payload,
    };
    writeIncidents([created, ...readIncidents()]);
    return Promise.resolve(created);
  },
  updateIncident: (id, payload) => {
    let updated = null;
    const incidents = readIncidents().map((incident) => {
      if (String(incident.id) !== String(id)) return incident;
      updated = {
        ...incident,
        ...payload,
        updated_at: new Date().toISOString(),
      };
      return updated;
    });
    writeIncidents(incidents);
    return Promise.resolve(updated);
  },
};
