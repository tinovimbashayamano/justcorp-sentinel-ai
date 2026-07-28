export const ALERT_STATUSES = ["unread", "acknowledged", "investigating", "resolved"];
export const ALERT_SEVERITIES = ["critical", "high", "medium", "low"];
export const SEVERITY_ORDER = { critical: 4, high: 3, medium: 2, low: 1 };

export function getAlertProbability(alert) {
  return Number(alert.fraud_probability ?? alert.probability ?? alert.fraud_score ?? 0);
}

export function classifyAlertSeverity(alert) {
  const explicit = String(alert.risk_band ?? "").trim().toLowerCase();
  if (ALERT_SEVERITIES.includes(explicit)) return explicit;
  const p = getAlertProbability(alert);
  if (p >= 0.9) return "critical";
  if (p >= 0.7) return "high";
  if (p >= 0.4) return "medium";
  return "low";
}

export function formatAlertProbability(alert) {
  return new Intl.NumberFormat("en-US", { style: "percent", maximumFractionDigits: 1 }).format(getAlertProbability(alert));
}

export function enrichAlerts(alerts = [], stateById = {}) {
  return alerts.map((alert) => {
    const state = stateById[alert.id] || {};
    return {
      ...alert,
      severity: classifyAlertSeverity(alert),
      alert_status: state.alert_status || "unread",
      acknowledged_at: state.acknowledged_at || null,
      assigned_at: state.assigned_at || null,
      investigating_at: state.investigating_at || null,
      resolved_at: state.resolved_at || null,
      assigned_analyst: state.assigned_analyst || alert.assigned_analyst || null,
    };
  });
}

function searchableText(alert) {
  return [alert.transaction_id, alert.customer_id, alert.merchant, alert.merchant_name, alert.product_code, alert.channel, alert.device_type, alert.model_version, alert.assigned_analyst].filter(Boolean).join(" ").toLowerCase();
}

export function filterAlerts(alerts = [], filters = {}) {
  const query = String(filters.query ?? "").trim().toLowerCase();
  const analyst = String(filters.analyst ?? "").trim().toLowerCase();
  return alerts.filter((alert) => {
    if (query && !searchableText(alert).includes(query)) return false;
    if (filters.severity && alert.severity !== filters.severity) return false;
    if (filters.status && alert.alert_status !== filters.status) return false;
    if (analyst && String(alert.assigned_analyst ?? "").trim().toLowerCase() !== analyst) return false;
    if (getAlertProbability(alert) < Number(filters.minimumProbability || 0)) return false;
    return true;
  });
}

export function sortAlerts(alerts = [], sort = {}) {
  const field = sort.field || "priority";
  const multiplier = sort.direction === "asc" ? 1 : -1;
  return [...alerts].sort((a, b) => {
    let x, y;
    if (field === "probability") { x = getAlertProbability(a); y = getAlertProbability(b); }
    else if (field === "severity" || field === "priority") { x = SEVERITY_ORDER[a.severity] || 0; y = SEVERITY_ORDER[b.severity] || 0; }
    else { x = new Date(a.created_at || 0).getTime(); y = new Date(b.created_at || 0).getTime(); }
    return (x - y) * multiplier;
  });
}

export function summarizeAlerts(alerts = []) {
  return alerts.reduce((s, a) => {
    s.total += 1; s[a.severity] += 1; s[a.alert_status] += 1; return s;
  }, { total: 0, unread: 0, acknowledged: 0, investigating: 0, resolved: 0, critical: 0, high: 0, medium: 0, low: 0 });
}

export function paginateAlerts(
  alerts = [],
  page = 1,
  pageSize = 20,
) {
  const safePageSize = Math.max(1, Number(pageSize) || 20);
  const totalItems = alerts.length;
  const totalPages = Math.max(
    1,
    Math.ceil(totalItems / safePageSize),
  );
  const safePage = Math.min(
    totalPages,
    Math.max(1, Number(page) || 1),
  );
  const startIndex = (safePage - 1) * safePageSize;

  return {
    items: alerts.slice(
      startIndex,
      startIndex + safePageSize,
    ),
    page: safePage,
    pageSize: safePageSize,
    totalItems,
    totalPages,
    startItem: totalItems ? startIndex + 1 : 0,
    endItem: Math.min(
      startIndex + safePageSize,
      totalItems,
    ),
  };
}

export function buildAlertTimeline(alert) {
  return [
    { label: "Alert created", timestamp: alert.created_at || null, complete: true },
    { label: "Acknowledged", timestamp: alert.acknowledged_at || null, complete: Boolean(alert.acknowledged_at) },
    { label: "Assigned", timestamp: alert.assigned_at || null, complete: Boolean(alert.assigned_at) },
    { label: "Investigation started", timestamp: alert.investigating_at || null, complete: Boolean(alert.investigating_at) },
    { label: "Resolved", timestamp: alert.resolved_at || null, complete: Boolean(alert.resolved_at) },
  ];
}

export function updateAlertState(currentState, alertId, status, analyst = null) {
  const now = new Date().toISOString();
  const next = { ...(currentState[alertId] || {}), alert_status: status };
  if (analyst) {
    next.assigned_analyst = analyst;
    next.assigned_at ||= now;
  }
  if (status === "acknowledged" && !next.acknowledged_at) next.acknowledged_at = now;
  if (status === "investigating") { next.acknowledged_at ||= now; next.investigating_at ||= now; }
  if (status === "resolved") { next.acknowledged_at ||= now; next.resolved_at = now; }
  return { ...currentState, [alertId]: next };
}
