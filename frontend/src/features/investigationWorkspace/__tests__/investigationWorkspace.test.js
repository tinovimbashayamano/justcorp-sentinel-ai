import { describe, expect, it } from "vitest";
import {
  buildSummary, buildTimeline, calculateTaskProgress,
  canTransitionStatus, normalizeAudit, sortNewest,
} from "../domain/investigationWorkspace";

describe("investigation workspace domain", () => {
  it("validates workflow transitions", () => {
    expect(canTransitionStatus("investigating", "resolved")).toBe(true);
    expect(canTransitionStatus("open", "assigned")).toBe(true);
    expect(canTransitionStatus("closed", "investigating")).toBe(false);
  });

  it("sorts newest first", () => {
    const result = sortNewest([
      { id: 1, created_at: "2026-07-27T10:00:00Z" },
      { id: 2, created_at: "2026-07-28T10:00:00Z" },
    ]);
    expect(result[0].id).toBe(2);
  });

  it("calculates task completion", () => {
    const result = calculateTaskProgress([
      { completed: true }, { completed: false },
      { completed: true }, { completed: false },
    ]);
    expect(result.completed).toBe(2);
    expect(result.percentage).toBe(50);
  });

  it("builds a case summary", () => {
    const result = buildSummary({
      id: "CASE-1",
      fraud_probability: 0.93,
      transaction_amount: 250,
    });
    expect(result.risk).toBe("critical");
    expect(result.amount).toBe(250);
  });

  it("combines timeline events", () => {
    const result = buildTimeline({
      timeline: [{ id: 1, title: "Opened", created_at: "2026-07-27T10:00:00Z" }],
      activity_history: [{ id: 2, action: "Assigned", created_at: "2026-07-28T10:00:00Z" }],
    });
    expect(result).toHaveLength(2);
    expect(result[0].title).toBe("Assigned");
  });

  it("normalizes audit entries", () => {
    const result = normalizeAudit([
      { id: 1, created_at: "2026-07-28T10:00:00Z", actor_name: "Analyst", action: "Status changed" },
    ]);
    expect(result[0].user).toBe("Analyst");
  });
});
