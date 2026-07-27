import { describe, expect, it } from "vitest";

import {
  buildCaseCreationPayload,
  filterAndSortCases,
  findCaseForScore,
  paginate,
  summarizeCases,
} from "../domain/caseQueue";

const scores = [
  {
    id: 1,
    transaction_id: "TX-100",
    fraud_probability: 0.9,
    risk_band: "high",
    merchant: "Store A",
  },
  {
    id: 2,
    transaction_id: "TX-200",
    fraud_probability: 0.4,
    risk_band: "medium",
    merchant: "Store B",
  },
];

const cases = [
  {
    id: 10,
    fraud_score_record_id: 1,
    case_status: "open",
    analyst_decision: "pending",
    reviewed_by: "Amina",
    updated_at: "2026-07-27T12:00:00Z",
  },
  {
    id: 11,
    fraud_score_record_id: 2,
    case_status: "closed",
    analyst_decision: "false_positive",
    reviewed_by: "Tino",
    updated_at: "2026-07-26T12:00:00Z",
  },
];

describe("smart case queue domain", () => {
  it("filters by transaction search", () => {
    const result = filterAndSortCases({
      cases,
      scores,
      filters: {
        query: "TX-100",
        status: "",
        decision: "",
        risk: "",
        analyst: "",
        minimumProbability: 0,
        dateFrom: "",
        dateTo: "",
      },
      sort: { field: "updated_at", direction: "desc" },
    });

    expect(result).toHaveLength(1);
    expect(result[0].id).toBe(10);
  });

  it("sorts by fraud probability", () => {
    const result = filterAndSortCases({
      cases,
      scores,
      filters: {
        query: "",
        status: "",
        decision: "",
        risk: "",
        analyst: "",
        minimumProbability: 0,
        dateFrom: "",
        dateTo: "",
      },
      sort: { field: "probability", direction: "desc" },
    });

    expect(result[0].id).toBe(10);
  });

  it("prevents duplicate lookup errors", () => {
    expect(findCaseForScore(cases, 1)?.id).toBe(10);
    expect(findCaseForScore(cases, 999)).toBeNull();
  });

  it("builds a default creation payload", () => {
    expect(buildCaseCreationPayload(1)).toEqual({
      fraud_score_record_id: 1,
      case_status: "open",
      analyst_decision: "pending",
      analyst_notes: null,
      reviewed_by: null,
    });
  });

  it("summarizes statuses", () => {
    const summary = summarizeCases(cases);
    expect(summary.open).toBe(1);
    expect(summary.closed).toBe(1);
  });

  it("paginates results", () => {
    const result = paginate([1, 2, 3, 4], 2, 2);
    expect(result.items).toEqual([3, 4]);
    expect(result.totalPages).toBe(2);
  });
});
