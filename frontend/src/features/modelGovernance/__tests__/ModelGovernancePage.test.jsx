import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import ModelGovernancePage from "../pages/ModelGovernancePage";

vi.mock("../hooks/useModelGovernance", () => ({
  useModelGovernance: () => ({
    summary: { registered_models: 3, production_models: 1, pending_approvals: 1, models_with_drift: 0, failed_training_runs: 0, active_experiments: 1 },
    champion: { id: "m1", name: "Fraud XGBoost", version: "v1.2" },
    championChallenger: { challengers: [] },
    visibleModels: [],
    filters: { search: "", status: "All", sortKey: "updated_at", sortDirection: "desc" },
    selectedModel: null,
    performance: {},
    drift: {},
    featureDrift: [],
    trainingRuns: [],
    datasets: [],
    deployments: [],
    auditTrail: [],
    modelCard: {},
    loading: false,
    detailLoading: false,
    actionLoading: false,
    error: null,
    setFilters: vi.fn(),
    load: vi.fn().mockResolvedValue(undefined),
    loadModelDetails: vi.fn(),
    approve: vi.fn(),
    reject: vi.fn(),
    promote: vi.fn(),
    rollback: vi.fn(),
  }),
}));

describe("ModelGovernancePage", () => {
  it("renders the governance dashboard", () => {
    render(<ModelGovernancePage />);
    expect(screen.getByRole("heading", { name: /Enterprise MLOps and model governance/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /Model registry/i })).toBeInTheDocument();
  });

  it("opens monitoring", () => {
    render(<ModelGovernancePage />);
    fireEvent.click(screen.getByRole("button", { name: "Monitoring" }));
    expect(screen.getByRole("heading", { name: /Feature drift/i })).toBeInTheDocument();
  });
});
