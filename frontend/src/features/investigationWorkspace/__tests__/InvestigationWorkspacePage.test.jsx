import {
  fireEvent,
  render,
  screen,
} from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { describe, expect, it, vi } from "vitest";
import InvestigationWorkspacePage from "../pages/InvestigationWorkspacePage";

const mocks = vi.hoisted(() => ({
  downloadEvidence: vi.fn(),
}));

vi.mock("../hooks/useInvestigationWorkspace", () => ({
  useInvestigationWorkspace: () => ({
    workspace: {
      investigation: {
        id: "CASE-1",
        fraud_score_record_id: 11,
        transaction_id: "TX-1",
      },
    },
    summary: {
      caseId: "CASE-1", transactionId: "TX-1", status: "investigating",
      priority: "high", risk: "high", probability: .82, amount: 300,
      currency: "USD", merchant: "Merchant A", customerId: "CUS-1",
      assignedAnalyst: "Ada Analyst", assignedAnalystId: "7", dueDate: null,
      modelVersion: "v1", deviceType: "mobile", location: "ZW",
      decision: "pending",
    },
    timeline: [{
      id: "timeline-1", title: "Customer contacted",
      created_at: "2026-07-28T09:12:00Z",
      description: "Contact attempt recorded", actor: "Ada Analyst",
    }],
    notes: [{
      id: "note-1", author_name: "Ada Analyst",
      created_at: "2026-07-28T09:15:00Z",
      content: "Customer unreachable.",
    }],
    evidence: [{
      id: "evidence-1", filename: "shap-report.pdf",
      uploader: "Ada Analyst", size: 1024,
      uploaded_at: "2026-07-28T09:30:00Z",
    }],
    tasks: [{
      id: "task-1", title: "Verify customer",
      status: "pending", completed: false,
    }],
    analysts: [{ id: "7", name: "Ada Analyst" }],
    activityHistory: [{
      id: "history-1", event_type: "case_viewed",
      actor_username: "Ada Analyst",
      created_at: "2026-07-28T09:10:00Z",
    }],
    taskProgress: { total: 1, completed: 0, percentage: 0 },
    auditLog: [{
      id: "audit-1", created_at: "2026-07-28T09:11:00Z",
      user: "Ada Analyst", action: "case_status_changed",
      previousValue: "assigned", newValue: "investigating",
      ipAddress: "127.0.0.1",
    }],
    loading: false, saving: false, error: null,
    loadWorkspace: vi.fn().mockResolvedValue({}), changeStatus: vi.fn(),
    changeAssignment: vi.fn(), createNote: vi.fn(), createTask: vi.fn(),
    toggleTask: vi.fn(), downloadEvidence: mocks.downloadEvidence,
  }),
}));

function renderWorkspace(extraRoutes = null) {
  render(
    <MemoryRouter
      initialEntries={["/fraud/investigations/CASE-1"]}
    >
      <Routes>
        <Route
          path="/fraud/investigations/:caseId"
          element={<InvestigationWorkspacePage />}
        />
        {extraRoutes}
      </Routes>
    </MemoryRouter>,
  );
}

describe("InvestigationWorkspacePage", () => {
  it("renders the workspace", () => {
    renderWorkspace();

    expect(screen.getByRole("heading", { name: /Case CASE-1/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /Investigation overview/i })).toBeInTheDocument();
    expect(screen.getByText("Merchant A")).toBeInTheDocument();
  });

  it("renders timeline and activity history", () => {
    renderWorkspace();

    expect(screen.getByText("Customer contacted")).toBeInTheDocument();
    expect(screen.getByText("Contact attempt recorded")).toBeInTheDocument();
    expect(screen.getByText("case viewed")).toBeInTheDocument();
  });

  it("renders analyst notes", () => {
    renderWorkspace();

    expect(screen.getByText("Customer unreachable.")).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/Markdown/i)).toBeInTheDocument();
  });

  it("renders evidence and downloads it", () => {
    renderWorkspace();

    expect(screen.getByText("shap-report.pdf")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Download" }));
    expect(mocks.downloadEvidence).toHaveBeenCalledWith(
      expect.objectContaining({ id: "evidence-1" }),
    );
  });

  it("renders task and assignment controls", () => {
    renderWorkspace();

    expect(screen.getByText("Verify customer")).toBeInTheDocument();
    expect(
      screen.getByRole("option", { name: "Ada Analyst" }),
    ).toBeInTheDocument();
  });

  it("renders audit history and explainability navigation", () => {
    renderWorkspace(
      <Route
        path="/fraud/explainability"
        element={<p>Explainability target</p>}
      />,
    );

    expect(screen.getByText("case_status_changed")).toBeInTheDocument();
    expect(screen.getByText("127.0.0.1")).toBeInTheDocument();

    fireEvent.click(
      screen.getByRole("button", {
        name: "Open explainability",
      }),
    );
    expect(
      screen.getByText("Explainability target"),
    ).toBeInTheDocument();
  });
});
