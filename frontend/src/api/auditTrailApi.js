import { httpClient } from "./httpClient";

const BASE = "/api/v1/audit-logs";
let eventCache = [];

function downloadBlob(blob, fileName) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = fileName;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

function csvCell(value) {
  const text =
    typeof value === "object"
      ? JSON.stringify(value ?? {})
      : String(value ?? "");
  return `"${text.replaceAll('"', '""')}"`;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function exportCsv(events) {
  const fields = [
    "created_at",
    "id",
    "actor_username",
    "action",
    "status",
    "resource_type",
    "resource_id",
    "ip_address",
    "user_agent",
    "details",
  ];
  const csv = [
    fields.join(","),
    ...events.map((event) =>
      fields.map((field) => csvCell(event[field])).join(","),
    ),
  ].join("\r\n");
  return new Blob([csv], { type: "text/csv;charset=utf-8" });
}

function printEvents(events) {
  const popup = window.open("", "_blank");
  if (!popup) {
    throw new Error(
      "The print preview was blocked. Allow pop-ups and try again.",
    );
  }
  popup.opener = null;
  const rows = events
    .map(
      (event) => `<tr>
        <td>${escapeHtml(event.created_at)}</td>
        <td>${escapeHtml(event.id)}</td>
        <td>${escapeHtml(event.actor_username ?? "System")}</td>
        <td>${escapeHtml(event.action)}</td>
        <td>${escapeHtml(event.status)}</td>
        <td>${escapeHtml(event.resource_type)}</td>
        <td>${escapeHtml(event.resource_id)}</td>
      </tr>`,
    )
    .join("");
  popup.document.write(`<!doctype html>
    <html><head><title>Audit trail export</title>
    <style>
      body{font:12px Arial,sans-serif;padding:24px;color:#172033}
      h1{font-size:22px}table{width:100%;border-collapse:collapse}
      th,td{border:1px solid #d7deea;padding:7px;text-align:left}
      th{background:#eef2f7}
    </style></head><body>
    <h1>JustCorp Sentinel AI — Audit Trail</h1>
    <p>Generated ${new Date().toLocaleString()} · ${events.length} records</p>
    <table><thead><tr><th>Timestamp</th><th>ID</th><th>User</th>
    <th>Action</th><th>Outcome</th><th>Resource</th><th>Resource ID</th>
    </tr></thead><tbody>${rows}</tbody></table></body></html>`);
  popup.document.close();
  popup.focus();
  popup.print();
}

export const auditTrailApi = {
  events: (params = {}) =>
    httpClient
      .get(BASE, {
        params: {
          limit: Math.min(Number(params.limit ?? 200), 200),
          offset: Number(params.offset ?? 0),
          action: params.action || undefined,
          status: params.status || undefined,
          actor_username: params.actor_username || undefined,
          resource_type: params.resource_type || undefined,
        },
      })
      .then((response) => {
        eventCache = response.data?.items ?? [];
        return response.data;
      }),
  event: (id) =>
    Promise.resolve(
      eventCache.find((event) => String(event.id) === String(id)) ?? null,
    ),
  summary: () => Promise.resolve({ available: false }),
  categories: () => Promise.resolve([]),
  actions: () => Promise.resolve([]),
  users: () => Promise.resolve([]),
  presets: () => Promise.resolve([]),
  integrity: () =>
    Promise.resolve({
      status: "Unavailable",
      available: false,
      reason: "The current backend does not store an audit hash chain.",
    }),
  retention: () =>
    Promise.resolve({
      available: false,
      reason: "No audit-retention endpoint is currently implemented.",
    }),
  verify: () =>
    Promise.reject(
      new Error(
        "Audit integrity verification is unavailable until backend hash-chain support is implemented.",
      ),
    ),
  export: async ({ format, events = [] }, fileName = "audit-export") => {
    const normalizedFormat = String(format).toLowerCase();
    if (normalizedFormat === "pdf") {
      printEvents(events);
      return true;
    }
    if (normalizedFormat === "csv") {
      downloadBlob(exportCsv(events), `${fileName}.csv`);
      return true;
    }
    if (normalizedFormat === "json") {
      downloadBlob(
        new Blob([JSON.stringify(events, null, 2)], {
          type: "application/json",
        }),
        `${fileName}.json`,
      );
      return true;
    }
    throw new Error(
      "XLSX audit export is unavailable until a backend exporter is implemented.",
    );
  },
};
