import { describe, expect, it } from "vitest";
import {
  createReportPayload,
  filterReports,
  formatBytes,
  normalizeCollection,
  normalizeSummary,
  reportTypeLabel,
  statusClass,
  validateReportForm,
} from "../domain/reports";

describe("report domain", () => {
  it("normalizes list envelopes", () => {
    expect(normalizeCollection({ items: [{ id: 1 }] })).toHaveLength(1);
  });
  it("normalizes summary defaults", () => {
    expect(normalizeSummary({}).total_reports).toBe(0);
  });
  it("formats bytes", () => {
    expect(formatBytes(1024)).toBe("1.0 KB");
  });
  it("maps report type labels", () => {
    expect(reportTypeLabel("audit_report")).toBe("Audit Report");
  });
  it("creates status classes", () => {
    expect(statusClass("Completed")).toBe("report-status-completed");
  });
  it("filters reports by status", () => {
    const reports = [
      { title: "A", status: "Completed" },
      { title: "B", status: "Failed" },
    ];
    expect(filterReports(reports, { status: "Failed" })).toHaveLength(1);
  });
  it("requires title, type and output format", () => {
    const errors = validateReportForm({
      reportType: "", outputFormat: "", title: "", dateFrom: "", dateTo: "",
    });
    expect(errors.reportType).toBeTruthy();
    expect(errors.outputFormat).toBeTruthy();
    expect(errors.title).toBeTruthy();
  });
  it("rejects invalid date ranges", () => {
    const errors = validateReportForm({
      reportType: "audit_report", outputFormat: "PDF", title: "Audit",
      dateFrom: "2026-07-20", dateTo: "2026-07-01",
    });
    expect(errors.dateTo).toBeTruthy();
  });
  it("creates generation payloads", () => {
    const payload = createReportPayload({
      reportType: "audit_report", outputFormat: "PDF", title: "Audit",
      description: "", dateFrom: "", dateTo: "", caseId: "",
      transactionId: "", modelId: "", severity: "",
      includeCharts: true, includeExplanations: true, includeAuditMetadata: true,
    });
    expect(payload.report_type).toBe("audit_report");
    expect(payload.output_format).toBe("pdf");
  });
});
