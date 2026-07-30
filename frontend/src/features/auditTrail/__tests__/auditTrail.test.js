import { describe, expect, it } from "vitest";
import {
  applyPreset, calculatePageRange, compareAuditChanges, DEFAULT_FILTERS,
  integrityClass, maskSensitiveValue, normalizeAuditCollection,
  normalizeAuditSummary, outcomeClass, serializeAuditFilters, severityClass,
} from "../domain/auditTrail";

describe("audit trail domain", () => {
  it("normalizes arrays", () => expect(normalizeAuditCollection([{ id: 1 }]).total).toBe(1));
  it("normalizes summary", () => expect(normalizeAuditSummary({}).total_events).toBe(0));
  it("serializes non-empty filters", () => expect(serializeAuditFilters({ search: "model", category: "" })).toEqual({ search: "model" }));
  it("builds severity classes", () => expect(severityClass("Critical")).toBe("audit-severity-critical"));
  it("builds outcome classes", () => expect(outcomeClass("Denied")).toBe("audit-outcome-denied"));
  it("builds integrity classes", () => expect(integrityClass("Integrity Warning")).toBe("audit-integrity-integrity-warning"));
  it("masks sensitive data", () => { expect(maskSensitiveValue("password", "x")).toBe("********"); expect(maskSensitiveValue("access_token", "x")).toBe("[REDACTED]"); });
  it("compares changes", () => expect(compareAuditChanges({ status: "Open" }, { status: "Closed" })[0].field).toBe("status"));
  it("calculates page ranges", () => expect(calculatePageRange(2, 25, 80)).toEqual({ start: 26, end: 50 }));
  it("applies presets", () => expect(applyPreset({ ...DEFAULT_FILTERS, page: 5 }, { filters: { severity: "Critical" } }).page).toBe(1));
});
