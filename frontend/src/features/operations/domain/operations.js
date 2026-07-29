export const DEFAULT_OPERATION_FILTERS = {
  environment: "all",
  time_range: "24h",
  log_level: "all",
  service: "all",
  search: "",
};

function optionalNumber(value) {
  return value == null || value === "" ? null : Number(value);
}

export function normalizeSummary(value = {}) {
  return {
    status: String(value.status ?? "unknown").toLowerCase(),
    uptime: Number(value.api_uptime ?? 0),
    averageLatency: Number(value.average_response_time_ms ?? 0),
    throughput: Number(value.requests_per_minute ?? 0),
    errorRate: Number(value.error_rate ?? 0),
    activeUsers: Number(value.active_users ?? 0),
    databaseConnections: optionalNumber(value.database_connections),
    queueBacklog: Number(value.queue_backlog ?? 0),
  };
}

export function normalizeServices(items = []) {
  return items.map((item) => ({
    id: item.id ?? item.name,
    name: item.name ?? "Unknown service",
    status: String(item.status ?? "unknown").toLowerCase(),
    responseTime: Number(item.response_time_ms ?? 0),
    uptime: Number(item.uptime ?? 0),
    lastCheck: item.last_health_check ?? null,
    version: item.version ?? "Not reported",
    environment: item.environment ?? "Not reported",
  }));
}

export function normalizeResources(value = {}) {
  return [
    ["CPU usage", value.cpu_usage],
    ["Memory usage", value.memory_usage],
    ["Disk usage", value.disk_usage],
    ["Database storage", value.database_storage_usage],
    ["Connection pool", value.connection_pool_usage],
    ["Worker utilization", value.worker_utilization],
  ].map(([label, rawValue]) => ({
    label,
    value: optionalNumber(rawValue),
  }));
}

export function sortIncidents(items = []) {
  const order = {
    critical: 5,
    high: 4,
    medium: 3,
    low: 2,
    informational: 1,
  };
  return [...items].sort(
    (a, b) =>
      (order[String(b.severity).toLowerCase()] ?? 0) -
        (order[String(a.severity).toLowerCase()] ?? 0) ||
      new Date(b.started_at ?? 0) - new Date(a.started_at ?? 0),
  );
}

export function sortJobs(items = []) {
  return [...items].sort(
    (a, b) =>
      new Date(b.started_at ?? 0) - new Date(a.started_at ?? 0),
  );
}

export function filterLogs(items = [], filters = {}) {
  const query = String(filters.search ?? "").toLowerCase();
  return items.filter(
    (item) =>
      (!filters.log_level ||
        filters.log_level === "all" ||
        String(item.level ?? "").toLowerCase() ===
          String(filters.log_level).toLowerCase()) &&
      (!filters.service ||
        filters.service === "all" ||
        String(item.service ?? "").toLowerCase() ===
          String(filters.service).toLowerCase()) &&
      (!query ||
        [
          item.message,
          item.request_id,
          item.user_id,
          item.endpoint,
          item.service,
        ].some((value) =>
          String(value ?? "").toLowerCase().includes(query),
        )),
  );
}

export function deriveOverallStatus(services = []) {
  if (!services.length) return "unknown";
  if (services.some((item) => item.status === "critical")) return "critical";
  if (services.some((item) => item.status === "degraded")) return "degraded";
  if (services.every((item) => item.status === "healthy")) return "healthy";
  return "unknown";
}

export function formatMetric(value, suffix = "") {
  return value == null || Number.isNaN(Number(value))
    ? "Not reported"
    : `${Number(value).toLocaleString("en-US", {
        maximumFractionDigits: 1,
      })}${suffix}`;
}
