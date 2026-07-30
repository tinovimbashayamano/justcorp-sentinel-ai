export const DEFAULT_FILTERS = {
  search: "", user: "", role: "", action: "", category: "", module: "",
  resource_type: "", resource_id: "", outcome: "", severity: "", source_ip: "",
  integrity_status: "", correlation_id: "", session_id: "", date_from: "", date_to: "",
  relative_range: "", page: 1, page_size: 25,
};

export const AUDIT_PRESETS = [
  { key: "failed_logins", label: "Failed Logins", filters: { category: "authentication", outcome: "Failure" } },
  { key: "administrative_changes", label: "Administrative Changes", filters: { category: "administration" } },
  { key: "critical_security_events", label: "Critical Security Events", filters: { category: "security", severity: "Critical" } },
  { key: "fraud_investigation_activity", label: "Fraud Investigation Activity", filters: { category: "investigation" } },
  { key: "model_deployment_activity", label: "Model Deployment Activity", filters: { category: "model_governance" } },
  { key: "report_downloads", label: "Report Downloads", filters: { action: "report.downloaded" } },
  { key: "permission_changes", label: "Permission Changes", filters: { action: "permission.changed" } },
  { key: "last_24_hours", label: "Last 24 Hours", filters: { relative_range: "24h" } },
  { key: "last_7_days", label: "Last 7 Days", filters: { relative_range: "7d" } },
];

const SENSITIVE_KEYS = ["password", "access_token", "refresh_token", "api_key", "secret", "authorization", "client_secret"];

export function normalizeAuditCollection(value) {
  if (Array.isArray(value)) return { items: value, page: 1, page_size: value.length || 25, total: value.length, total_pages: 1 };
  return {
    items: Array.isArray(value?.items) ? value.items : [],
    page: Number(value?.page ?? 1),
    page_size: Number(value?.page_size ?? 25),
    total: Number(value?.total ?? value?.items?.length ?? 0),
    total_pages: Number(value?.total_pages ?? 1),
  };
}

function titleCase(value, fallback = "Unknown") {
  const text = String(value ?? "").trim();
  if (!text) return fallback;
  return text.charAt(0).toUpperCase() + text.slice(1).toLowerCase();
}

function categoryForAction(action = "") {
  if (action.startsWith("auth.")) return "authentication";
  if (action.startsWith("admin.")) return "administration";
  if (action.startsWith("fraud.")) return "fraud_monitoring";
  if (
    action.startsWith("case.") ||
    action.startsWith("investigation_task.")
  ) {
    return "investigation";
  }
  if (action.startsWith("model.")) return "model_governance";
  if (action.startsWith("report.")) return "reports";
  return "platform_operations";
}

function severityForEvent(event) {
  if (event.status === "failure" || event.status === "denied") return "High";
  if (
    event.action?.startsWith("admin.") ||
    event.action?.includes("delete") ||
    event.action?.includes("password")
  ) {
    return "Medium";
  }
  return "Informational";
}

export function maskSensitiveObject(value) {
  if (Array.isArray(value)) return value.map(maskSensitiveObject);
  if (!value || typeof value !== "object") return value;
  return Object.fromEntries(
    Object.entries(value).map(([key, nested]) => {
      const masked = maskSensitiveValue(key, nested);
      if (masked === "********" || masked === "[REDACTED]") {
        return [key, masked];
      }
      return [
        key,
        nested && typeof nested === "object"
          ? maskSensitiveObject(nested)
          : nested,
      ];
    }),
  );
}

function extractChanges(details = {}) {
  if (details.before || details.after) {
    return {
      before: details.before ?? {},
      after: details.after ?? {},
    };
  }
  const before = {};
  const after = {};
  for (const [key, value] of Object.entries(details)) {
    if (key.startsWith("old_")) before[key.slice(4)] = value;
    if (key.startsWith("new_")) after[key.slice(4)] = value;
  }
  return { before, after };
}

export function normalizeAuditEvent(value = {}) {
  const details = value.details ?? {};
  const changes = extractChanges(details);
  const category = value.category ?? categoryForAction(value.action);
  return {
    ...value,
    details: maskSensitiveObject(details),
    timestamp: value.timestamp ?? value.created_at,
    actor: value.actor ?? {
      user_id: value.user_id,
      email: value.actor_username,
      role: details.actor_role,
    },
    category,
    module: value.module ?? String(value.action ?? "").split(".")[0],
    outcome: titleCase(value.outcome ?? value.status),
    severity: value.severity ?? severityForEvent(value),
    source_ip: value.source_ip ?? value.ip_address,
    description:
      value.description ??
      details.description ??
      String(value.action ?? "").replaceAll(".", " "),
    before: value.before ?? changes.before,
    after: value.after ?? changes.after,
    metadata: maskSensitiveObject(value.metadata ?? details),
    integrity: value.integrity ?? {
      status: "Legacy Record",
      available: false,
    },
  };
}

function includesText(value, query) {
  return String(value ?? "").toLowerCase().includes(query);
}

function equalsText(value, expected) {
  return !expected ||
    String(value ?? "").toLowerCase() === String(expected).toLowerCase();
}

export function filterAuditEvents(events = [], filters = {}) {
  const query = String(filters.search ?? "").trim().toLowerCase();
  const now = Date.now();
  const relativeCutoff =
    filters.relative_range === "24h"
      ? now - 24 * 60 * 60 * 1000
      : filters.relative_range === "7d"
        ? now - 7 * 24 * 60 * 60 * 1000
        : null;
  return events.filter((event) => {
    const timestamp = new Date(event.timestamp ?? event.created_at).getTime();
    const queryValues = [
      event.id,
      eventActorLabel(event),
      event.action,
      event.category,
      event.module,
      event.resource_type,
      event.resource_id,
      event.source_ip,
      event.description,
      event.correlation_id,
      event.session_id,
    ];
    return (
      (!query || queryValues.some((value) => includesText(value, query))) &&
      (!filters.user ||
        includesText(eventActorLabel(event), String(filters.user).toLowerCase())) &&
      equalsText(event.actor?.role ?? event.user_role, filters.role) &&
      equalsText(event.action, filters.action) &&
      equalsText(event.category, filters.category) &&
      equalsText(event.module, filters.module) &&
      equalsText(event.resource_type, filters.resource_type) &&
      (!filters.resource_id ||
        includesText(event.resource_id, String(filters.resource_id).toLowerCase())) &&
      equalsText(event.outcome, filters.outcome) &&
      equalsText(event.severity, filters.severity) &&
      equalsText(event.source_ip, filters.source_ip) &&
      equalsText(
        event.integrity?.status ?? event.integrity_status,
        filters.integrity_status,
      ) &&
      (!filters.correlation_id ||
        includesText(event.correlation_id, filters.correlation_id.toLowerCase())) &&
      (!filters.session_id ||
        includesText(event.session_id, filters.session_id.toLowerCase())) &&
      (!filters.date_from ||
        timestamp >= new Date(filters.date_from).getTime()) &&
      (!filters.date_to || timestamp <= new Date(filters.date_to).getTime()) &&
      (!relativeCutoff || timestamp >= relativeCutoff)
    );
  });
}

export function summarizeAuditEvents(events = []) {
  const lastDay = Date.now() - 24 * 60 * 60 * 1000;
  return normalizeAuditSummary({
    total_events: events.length,
    security_events: events.filter((event) =>
      ["authentication", "security"].includes(event.category),
    ).length,
    failed_authentication_attempts: events.filter(
      (event) =>
        event.category === "authentication" &&
        ["Failure", "Denied"].includes(event.outcome),
    ).length,
    administrative_changes: events.filter(
      (event) => event.category === "administration",
    ).length,
    high_risk_actions: events.filter((event) =>
      ["High", "Critical"].includes(event.severity),
    ).length,
    export_download_events: events.filter((event) =>
      /(export|download)/i.test(event.action),
    ).length,
    unique_users: new Set(
      events.map(eventActorLabel).filter((value) => value !== "System"),
    ).size,
    events_last_24_hours: events.filter(
      (event) =>
        new Date(event.timestamp ?? event.created_at).getTime() >= lastDay,
    ).length,
  });
}

export function buildAuditLookups(events = []) {
  const unique = (values) =>
    [...new Set(values.filter(Boolean))].sort((a, b) =>
      String(a).localeCompare(String(b)),
    );
  return {
    categories: unique(events.map((event) => event.category)),
    actions: unique(events.map((event) => event.action)),
    users: unique(events.map(eventActorLabel)).map((email) => ({ email })),
    presets: [],
  };
}

export function paginateAuditEvents(events = [], page = 1, pageSize = 25) {
  const size = Math.max(1, Number(pageSize) || 25);
  const totalPages = Math.max(1, Math.ceil(events.length / size));
  const currentPage = Math.min(Math.max(1, Number(page) || 1), totalPages);
  const start = (currentPage - 1) * size;
  return {
    items: events.slice(start, start + size),
    page: currentPage,
    page_size: size,
    total: events.length,
    total_pages: totalPages,
  };
}

export function normalizeAuditSummary(value = {}) {
  return {
    total_events: 0, security_events: 0, failed_authentication_attempts: 0,
    administrative_changes: 0, high_risk_actions: 0, export_download_events: 0,
    unique_users: 0, events_last_24_hours: 0, ...value,
  };
}

export function serializeAuditFilters(filters = {}) {
  return Object.fromEntries(Object.entries(filters).filter(([, v]) => v !== "" && v !== null && v !== undefined));
}

export function severityClass(v = "") { return `audit-severity-${String(v).toLowerCase().replaceAll(" ", "-")}`; }
export function outcomeClass(v = "") { return `audit-outcome-${String(v).toLowerCase().replaceAll(" ", "-")}`; }
export function integrityClass(v = "") { return `audit-integrity-${String(v).toLowerCase().replaceAll(" ", "-")}`; }

export function formatAuditDate(value) {
  if (!value) return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return String(value);
  return new Intl.DateTimeFormat("en-US", { dateStyle: "medium", timeStyle: "medium" }).format(d);
}

export function maskSensitiveValue(key, value) {
  const normalized = String(key ?? "").toLowerCase();
  if (SENSITIVE_KEYS.some((k) => normalized.includes(k))) return normalized.includes("password") ? "********" : "[REDACTED]";
  if (value === null || value === undefined) return "—";
  return typeof value === "object" ? JSON.stringify(value, null, 2) : String(value);
}

export function compareAuditChanges(before = {}, after = {}) {
  const keys = [...new Set([...Object.keys(before || {}), ...Object.keys(after || {})])];
  return keys
    .filter((k) => JSON.stringify(before?.[k]) !== JSON.stringify(after?.[k]))
    .map((k) => ({ field: k, before: maskSensitiveValue(k, before?.[k]), after: maskSensitiveValue(k, after?.[k]) }));
}

export function eventActorLabel(event = {}) {
  return event.actor?.email || event.actor?.name || event.actor?.user_id || event.user_email || event.user_id || "System";
}

export function calculatePageRange(page, pageSize, total) {
  if (!total) return { start: 0, end: 0 };
  return { start: (page - 1) * pageSize + 1, end: Math.min(page * pageSize, total) };
}

export function applyPreset(current, preset) {
  return { ...DEFAULT_FILTERS, ...current, ...preset.filters, page: 1 };
}
