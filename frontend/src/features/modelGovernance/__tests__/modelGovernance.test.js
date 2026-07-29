import { describe, expect, it } from "vitest";
import {
  determineDriftState,
  filterModels,
  normalizeMetric,
  normalizePercent,
  normalizeSummary,
  selectChampion,
  sortModels,
  statusClass,
} from "../domain/modelGovernance";

describe("model governance domain", () => {
  it("normalizes summary defaults", () => expect(normalizeSummary({}).registered_models).toBe(0));
  it("formats metrics", () => expect(normalizeMetric(0.91234)).toBe("0.912"));
  it("formats percentages", () => expect(normalizePercent(0.25)).toBe("25%"));
  it("creates status classes", () => expect(statusClass("Pending Approval")).toBe("status-pending-approval"));
  it("filters by query", () => expect(filterModels([{ name: "Fraud XGBoost", status: "Production" }], "xgboost", "All")).toHaveLength(1));
  it("filters by status", () => expect(filterModels([{ name: "A", status: "Production" }, { name: "B", status: "Draft" }], "", "Draft")).toHaveLength(1));
  it("sorts descending", () => expect(sortModels([{ id: 1, pr_auc: 0.5 }, { id: 2, pr_auc: 0.8 }], "pr_auc", "desc")[0].id).toBe(2));
  it("detects warning drift", () => expect(determineDriftState(0.15)).toBe("Warning"));
  it("detects critical drift", () => expect(determineDriftState(0.3)).toBe("Critical"));
  it("selects production champion", () => expect(selectChampion([{ id: 1, status: "Challenger" }, { id: 2, status: "Production" }]).id).toBe(2));
});
