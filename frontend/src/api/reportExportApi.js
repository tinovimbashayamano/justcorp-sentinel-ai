import { httpClient } from "./httpClient";

const BASE = "/api/v1/reports";
const SCHEDULES_STORAGE_KEY = "sentinel_report_schedules";

export const REPORT_TEMPLATES = [
  {
    id: "complete-case",
    name: "Complete fraud investigation",
    description: "Case summary, investigation activity, evidence and audit context.",
    report_type: "fraud_investigation",
    version: "1.0",
  },
  {
    id: "investigation-timeline",
    name: "Investigation timeline",
    description: "Chronological case activity prepared for review.",
    report_type: "investigation_timeline",
    version: "1.0",
  },
  {
    id: "audit-summary",
    name: "Case audit summary",
    description: "Audit-focused record for a single fraud case.",
    report_type: "audit_report",
    version: "1.0",
  },
];

export const REPORT_TYPE_CAPABILITIES = [
  { report_type: "fraud_investigation", formats: ["pdf"] },
  { report_type: "investigation_timeline", formats: ["pdf", "csv"] },
  { report_type: "audit_report", formats: ["pdf", "csv"] },
];

const BACKEND_REPORT_TYPES = {
  fraud_investigation: "complete_case",
  investigation_timeline: "investigation_timeline",
  audit_report: "audit_summary",
};

function readSchedules() {
  try {
    return JSON.parse(window.localStorage.getItem(SCHEDULES_STORAGE_KEY) || "[]");
  } catch {
    return [];
  }
}

function writeSchedules(schedules) {
  window.localStorage.setItem(
    SCHEDULES_STORAGE_KEY,
    JSON.stringify(schedules),
  );
}

function normalizeCaseId(value) {
  const caseId = Number(value);
  if (!Number.isInteger(caseId) || caseId < 1) {
    throw new Error("A valid case ID is required for server-generated reports.");
  }
  return caseId;
}

export const reportExportApi = {
  list: (params = {}) =>
    httpClient
      .get(BASE, { params: { limit: 100, ...params } })
      .then((response) => response.data),
  history: (params = {}) =>
    httpClient
      .get(BASE, { params: { limit: 100, ...params } })
      .then((response) => response.data),
  report: (id) =>
    httpClient.get(`${BASE}/${id}`).then((response) => response.data),
  generate: (payload) => {
    const reportType = BACKEND_REPORT_TYPES[payload.report_type];
    if (!reportType) {
      return Promise.reject(
        new Error(
          "This report type needs a backend generator that has not been implemented yet.",
        ),
      );
    }

    const caseId = normalizeCaseId(payload.filters?.case_id);
    return httpClient
      .post(`${BASE}/cases/${caseId}`, {
        report_type: reportType,
        export_format: payload.output_format,
        title: payload.title,
        include_sensitive_data: false,
        include_internal_comments: Boolean(
          payload.filters?.include_explanations,
        ),
        include_audit_logs: Boolean(
          payload.filters?.include_audit_metadata,
        ),
      })
      .then((response) => response.data?.report ?? response.data);
  },
  remove: (id) =>
    httpClient.delete(`${BASE}/${id}`).then((response) => response.data),
  templates: () => Promise.resolve(REPORT_TEMPLATES),
  types: () => Promise.resolve(REPORT_TYPE_CAPABILITIES),
  scheduled: () => Promise.resolve(readSchedules()),
  schedule: (payload) => {
    const created = {
      ...payload,
      id: crypto.randomUUID(),
      created_at: new Date().toISOString(),
      next_run_at: null,
      storage: "browser",
    };
    const schedules = [created, ...readSchedules()];
    writeSchedules(schedules);
    return Promise.resolve(created);
  },
  cancelSchedule: (id) => {
    writeSchedules(readSchedules().filter((item) => item.id !== id));
    return Promise.resolve({ id });
  },
  download: async (id, fileName = "report") => {
    const response = await httpClient.get(`${BASE}/${id}/download`, {
      responseType: "blob",
    });
    const url = URL.createObjectURL(response.data);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = fileName;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
    return true;
  },
};
