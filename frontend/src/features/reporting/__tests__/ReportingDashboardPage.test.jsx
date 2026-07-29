import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import ReportingDashboardPage from "../pages/ReportingDashboardPage";

vi.mock("../hooks/useReportingDashboard", () => ({
  useReportingDashboard: () => ({
    filters: { date_from: "", date_to: "", department: "all", risk_level: "all" },
    loading: false,
    exporting: false,
    error: null,
    loadDashboard: vi.fn().mockResolvedValue({}),
    downloadReport: vi.fn(),
    addSchedule: vi.fn(),
    removeSchedule: vi.fn(),
    schedules: [],
    auditEvidence: [],
    modelPerformance: {},
    summary: {
      transactionsReviewed: 100,
      fraudCases: 10,
      fraudPrevented: 50000,
      openInvestigations: 5,
      closedInvestigations: 20,
      averageReviewHours: 2.5,
      highRiskAlerts: 4,
      precision: 0.9,
      recall: 0.8,
    },
    trends: [],
    riskDistribution: [
      { riskLevel: "critical", count: 2 },
      { riskLevel: "high", count: 4 },
      { riskLevel: "medium", count: 8 },
      { riskLevel: "low", count: 12 },
    ],
    cases: [],
    analysts: [],
    compliance: [],
  }),
}));

describe("ReportingDashboardPage", () => {
  it("renders reporting sections", () => {
    render(<ReportingDashboardPage />);
    expect(screen.getByRole("heading", {
      name: /Executive reporting and compliance/i,
    })).toBeInTheDocument();
    expect(screen.getByRole("heading", {
      name: /Fraud and alert trends/i,
    })).toBeInTheDocument();
    expect(screen.getByRole("heading", {
      name: /Case performance/i,
    })).toBeInTheDocument();
    expect(screen.getByRole("heading", {
      name: /Scheduled reports/i,
    })).toBeInTheDocument();
  });
});
