export const MODEL_STATUSES = [
  "Draft", "Training", "Validated", "Pending Approval", "Approved",
  "Production", "Challenger", "Archived", "Rejected", "Failed",
];

export function normalizeSummary(value = {}) {
  return {
    registered_models: 0,
    production_models: 0,
    pending_approvals: null,
    models_with_drift: null,
    failed_training_runs: null,
    active_experiments: null,
    latest_deployment: null,
    champion_model: null,
    ...value,
  };
}

export function normalizeMetric(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "Not reported";
  return Number(value).toFixed(3);
}

export function normalizePercent(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "Not reported";
  const numeric = Number(value);
  return `${numeric <= 1 ? numeric * 100 : numeric}%`;
}

export function statusClass(status = "") {
  return `status-${String(status).toLowerCase().replaceAll(" ", "-")}`;
}

export function driftClass(status = "") {
  return `drift-${String(status).toLowerCase().replaceAll(" ", "-")}`;
}

export function sortModels(models = [], key = "updated_at", direction = "desc") {
  return [...models].sort((a, b) => {
    const left = a?.[key];
    const right = b?.[key];
    if (key.endsWith("_at") || key.includes("date")) {
      const diff = new Date(left ?? 0) - new Date(right ?? 0);
      return direction === "asc" ? diff : -diff;
    }
    if (typeof left === "number" && typeof right === "number") {
      return direction === "asc" ? left - right : right - left;
    }
    return direction === "asc"
      ? String(left ?? "").localeCompare(String(right ?? ""))
      : String(right ?? "").localeCompare(String(left ?? ""));
  });
}

export function filterModels(models = [], query = "", status = "All") {
  const normalized = query.trim().toLowerCase();
  return models.filter((model) => {
    const matchesStatus = status === "All" || model.status === status;
    const matchesQuery = !normalized || [
      model.name, model.version, model.algorithm, model.owner, model.environment
    ].some((value) => String(value ?? "").toLowerCase().includes(normalized));
    return matchesStatus && matchesQuery;
  });
}

export function determineDriftState(score, warning = 0.1, critical = 0.25) {
  if (score === null || score === undefined || score === "") return "Unknown";
  const numeric = Number(score);
  if (Number.isNaN(numeric)) return "Unknown";
  if (numeric >= critical) return "Critical";
  if (numeric >= warning) return "Warning";
  return "Stable";
}

export function selectChampion(models = []) {
  return models.find((model) => model.status === "Production")
    ?? [...models].sort((a, b) => (b.pr_auc ?? 0) - (a.pr_auc ?? 0))[0]
    ?? null;
}
