export const REPORT_TYPES = [
  { key: "fraud_investigation", label: "Fraud Investigation Report", description: "Complete case, evidence, scoring and analyst decision record.", formats: ["PDF", "XLSX"], availableFormats: ["PDF"] },
  { key: "executive_fraud_summary", label: "Executive Fraud Summary", description: "Management-level fraud KPIs, financial impact and trends.", formats: ["PDF"], availableFormats: [] },
  { key: "transaction_report", label: "Transaction Report", description: "Filtered transaction search results and fraud scores.", formats: ["PDF", "XLSX", "CSV"], availableFormats: [] },
  { key: "alert_report", label: "Alert Report", description: "Alert severity, assignment, status and resolution details.", formats: ["PDF", "XLSX"], availableFormats: [] },
  { key: "investigation_timeline", label: "Investigation Timeline Report", description: "Chronological actions, notes, attachments and assignments.", formats: ["PDF"], availableFormats: ["PDF"] },
  { key: "model_performance", label: "Model Performance Report", description: "Metrics, drift, deployment and champion/challenger performance.", formats: ["PDF", "XLSX"], availableFormats: [] },
  { key: "model_card", label: "Model Card", description: "Purpose, limitations, data, bias, monitoring and approval record.", formats: ["PDF"], availableFormats: [] },
  { key: "audit_report", label: "Audit Report", description: "User actions, resources, IP addresses and timestamps.", formats: ["PDF", "XLSX", "CSV"], availableFormats: ["PDF", "CSV"] },
  { key: "operations_report", label: "Operations Report", description: "Availability, latency, errors, infrastructure and service health.", formats: ["PDF"], availableFormats: [] },
];

export function normalizeCollection(value) {
  if (Array.isArray(value)) return value;
  if (Array.isArray(value?.items)) return value.items;
  return [];
}

export function normalizeSummary(value = {}) {
  return {
    total_reports: 0,
    completed_reports: 0,
    failed_reports: 0,
    scheduled_reports: 0,
    downloads_this_month: 0,
    storage_used_mb: 0,
    ...value,
  };
}

export function normalizeReport(report = {}) {
  const status = String(report.status ?? "pending");
  return {
    ...report,
    output_format: report.output_format ?? report.export_format,
    created_by:
      report.created_by ??
      report.generated_by_username ??
      (report.generated_by_user_id
        ? `User ${report.generated_by_user_id}`
        : "Unknown"),
    file_name: report.file_name ?? report.stored_filename,
    status: status.charAt(0).toUpperCase() + status.slice(1).toLowerCase(),
  };
}

export function summarizeReports(reports = [], scheduledCount = 0) {
  const completed = reports.filter((item) => item.status === "Completed");
  return normalizeSummary({
    total_reports: reports.length,
    completed_reports: completed.length,
    failed_reports: reports.filter((item) => item.status === "Failed").length,
    scheduled_reports: scheduledCount,
    downloads_this_month: reports.reduce(
      (total, item) => total + Number(item.download_count ?? 0),
      0,
    ),
    storage_used_mb: Number(
      (
        reports.reduce(
          (total, item) => total + Number(item.file_size_bytes ?? 0),
          0,
        ) /
        1024 /
        1024
      ).toFixed(1),
    ),
  });
}

export function statusClass(status = "") {
  return `report-status-${String(status).toLowerCase().replaceAll(" ", "-")}`;
}

export function formatBytes(bytes) {
  const value = Number(bytes);
  if (!Number.isFinite(value) || value < 0) return "—";
  if (value === 0) return "0 B";
  const units = ["B", "KB", "MB", "GB"];
  const index = Math.min(Math.floor(Math.log(value) / Math.log(1024)), units.length - 1);
  return `${(value / 1024 ** index).toFixed(index === 0 ? 0 : 1)} ${units[index]}`;
}

export function formatDateTime(value) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

export function reportTypeLabel(key) {
  return REPORT_TYPES.find((type) => type.key === key)?.label ?? key ?? "Unknown";
}

export function createReportPayload(form) {
  return {
    report_type: form.reportType,
    output_format: form.outputFormat.toLowerCase(),
    title: form.title.trim(),
    description: form.description.trim() || null,
    date_from: form.dateFrom || null,
    date_to: form.dateTo || null,
    filters: {
      case_id: form.caseId.trim() || null,
      transaction_id: form.transactionId.trim() || null,
      model_id: form.modelId.trim() || null,
      severity: form.severity || null,
      include_charts: form.includeCharts,
      include_explanations: form.includeExplanations,
      include_audit_metadata: form.includeAuditMetadata,
    },
  };
}

export function validateReportForm(form) {
  const errors = {};
  if (!form.reportType) errors.reportType = "Select a report type.";
  if (!form.outputFormat) errors.outputFormat = "Select an output format.";
  if (!form.title.trim()) errors.title = "Enter a report title.";
  if (form.dateFrom && form.dateTo && form.dateFrom > form.dateTo) {
    errors.dateTo = "The end date cannot be earlier than the start date.";
  }
  const type = REPORT_TYPES.find((item) => item.key === form.reportType);
  if (type && form.outputFormat && !type.formats.includes(form.outputFormat)) {
    errors.outputFormat = `${form.outputFormat} is not supported for this report.`;
  }
  if (type && type.availableFormats.length === 0) {
    errors.reportType =
      "The backend generator for this report type is not available yet.";
  } else if (
    type &&
    form.outputFormat &&
    !type.availableFormats.includes(form.outputFormat)
  ) {
    errors.outputFormat =
      `${form.outputFormat} is planned but is not supported by the backend yet.`;
  }
  if (
    type?.availableFormats.length > 0 &&
    !String(form.caseId ?? "").trim()
  ) {
    errors.caseId = "Enter the fraud case ID to generate this report.";
  }
  return errors;
}

export function filterReports(reports = [], filters = {}) {
  const query = String(filters.search ?? "").trim().toLowerCase();
  return reports.filter((report) => {
    const matchesQuery =
      !query ||
      [report.title, report.report_type, report.created_by, report.id].some(
        (value) => String(value ?? "").toLowerCase().includes(query)
      );
    const matchesStatus =
      !filters.status || filters.status === "All" || report.status === filters.status;
    const matchesFormat =
      !filters.format ||
      filters.format === "All" ||
      String(report.output_format ?? "").toUpperCase() === filters.format;
    return matchesQuery && matchesStatus && matchesFormat;
  });
}
