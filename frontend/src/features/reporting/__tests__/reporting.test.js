import { describe, expect, it } from "vitest";
import {
  buildTrendSeries,
  calculateResolutionRate,
  normalizeCompliance,
  normalizeRiskDistribution,
  normalizeSummary,
  sortAnalysts,
  sortCases,
} from "../domain/reporting";

describe("reporting domain", () => {
  it("normalizes summary values", () => {
    const result = normalizeSummary({
      transactions_reviewed: 100,
      fraud_amount_prevented: 25000,
    });
    expect(result.transactionsReviewed).toBe(100);
    expect(result.fraudPrevented).toBe(25000);
  });

  it("defaults missing summary metrics to zero", () => {
    const result = normalizeSummary();
    expect(result.openInvestigations).toBe(0);
    expect(result.averageReviewHours).toBe(0);
    expect(result.precision).toBe(0);
  });

  it("calculates resolution rate", () => {
    expect(calculateResolutionRate({
      openInvestigations: 20,
      closedInvestigations: 80,
    })).toBe(80);
  });

  it("returns zero resolution rate when no cases exist", () => {
    expect(calculateResolutionRate()).toBe(0);
  });

  it("sorts cases newest first", () => {
    const result = sortCases([
      { id: 1, opened_at: "2026-07-27" },
      { id: 2, opened_at: "2026-07-28" },
    ]);
    expect(result[0].id).toBe(2);
  });

  it("sorts analysts by completed cases", () => {
    const result = sortAnalysts([
      { id: 1, cases_completed: 3 },
      { id: 2, cases_completed: 8 },
    ]);
    expect(result[0].id).toBe(2);
  });

  it("normalizes risk distribution", () => {
    const result = normalizeRiskDistribution([
      { risk_level: "high", count: 5 },
      { risk_level: "low", count: 10 },
    ]);
    expect(result.find((item) => item.riskLevel === "high").count).toBe(5);
  });

  it("supports alternate risk distribution value fields", () => {
    const result = normalizeRiskDistribution([
      { label: "critical", value: 3 },
      { label: "medium", value: 7 },
    ]);
    expect(result.find((item) => item.riskLevel === "critical").count).toBe(3);
    expect(result.find((item) => item.riskLevel === "medium").count).toBe(7);
  });

  it("normalizes compliance controls", () => {
    const result = normalizeCompliance({
      audit_log_coverage: 95,
      explainability_coverage: 65,
    });
    expect(result[0].status).toBe("compliant");
    expect(result[1].status).toBe("non_compliant");
  });

  it("marks mid-range compliance controls for attention", () => {
    const result = normalizeCompliance({
      audit_log_coverage: 75,
    });
    expect(result[0].status).toBe("attention");
  });

  it("sorts trend data chronologically", () => {
    const result = buildTrendSeries([
      { date: "2026-07-28", alerts: 8 },
      { date: "2026-07-27", alerts: 3 },
    ]);
    expect(result[0].date).toBe("2026-07-27");
  });

  it("normalizes trend metric values to numbers", () => {
    const result = buildTrendSeries([
      { date: "2026-07-27", alerts: "3", confirmed_fraud: "2" },
    ]);
    expect(result[0].alerts).toBe(3);
    expect(result[0].confirmedFraud).toBe(2);
  });

  it("keeps analyst sorting stable for missing completion counts", () => {
    const result = sortAnalysts([{ id: 1 }, { id: 2, cases_completed: 1 }]);
    expect(result[0].id).toBe(2);
  });
});
