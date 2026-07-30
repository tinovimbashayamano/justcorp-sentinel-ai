import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import ReportExportDashboard from "../pages/ReportExportDashboard";

vi.mock("../hooks/useReportExports", () => ({
  useReportExports: () => ({
    summary: {
      total_reports: 4, completed_reports: 3, failed_reports: 0,
      scheduled_reports: 1, downloads_this_month: 10, storage_used_mb: 12,
    },
    visibleReports: [], templates: [], scheduled: [], selectedReport: null,
    filters: { search: "", status: "All", format: "All" },
    loading: false, actionLoading: false, error: null,
    load: vi.fn().mockResolvedValue(undefined), generate: vi.fn(),
    remove: vi.fn(), schedule: vi.fn(), cancelSchedule: vi.fn(),
    download: vi.fn(), selectReport: vi.fn(), setFilters: vi.fn(),
  }),
}));

describe("ReportExportDashboard", () => {
  it("renders the report dashboard", () => {
    render(<ReportExportDashboard />);
    expect(screen.getByRole("heading", {
      name: /Enterprise report generation/i,
    })).toBeInTheDocument();
    expect(screen.getByText("Completed reports")).toBeInTheDocument();
  });

  it("opens the generation form", () => {
    render(<ReportExportDashboard />);
    fireEvent.click(screen.getByRole("button", { name: "Generate" }));
    expect(screen.getByRole("heading", {
      name: /Generate report/i,
    })).toBeInTheDocument();
  });
});
