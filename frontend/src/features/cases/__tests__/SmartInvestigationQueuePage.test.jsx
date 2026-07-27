import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import SmartInvestigationQueuePage from "../pages/SmartInvestigationQueuePage";

vi.mock("../hooks/useSmartCaseQueue", () => ({
  useSmartCaseQueue: () => ({
    cases: [],
    scores: [],
    selectedCase: null,
    selectedScore: null,
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
    sort: { field: "updated_at", direction: "desc" },
    pageSize: 10,
    pagination: {
      items: [],
      page: 1,
      pageSize: 10,
      totalItems: 0,
      totalPages: 1,
    },
    summary: {
      total: 0,
      open: 0,
      under_review: 0,
      confirmed_fraud: 0,
      false_positive: 0,
      closed: 0,
    },
    loading: {},
    error: null,
    loadQueue: vi.fn().mockResolvedValue(undefined),
    selectCase: vi.fn(),
    saveCase: vi.fn(),
    openOrCreateCase: vi.fn(),
    updateFilters: vi.fn(),
    clearFilters: vi.fn(),
    setSort: vi.fn(),
    setPage: vi.fn(),
    setPageSize: vi.fn(),
  }),
}));

describe("SmartInvestigationQueuePage", () => {
  it("renders the queue workspace", () => {
    render(<SmartInvestigationQueuePage />);

    expect(
      screen.getByRole("heading", {
        name: /Smart Investigation Queue/i,
      })
    ).toBeInTheDocument();

    expect(
      screen.getByRole("heading", {
        name: /Alert-to-case workflow/i,
      })
    ).toBeInTheDocument();
  });
});
