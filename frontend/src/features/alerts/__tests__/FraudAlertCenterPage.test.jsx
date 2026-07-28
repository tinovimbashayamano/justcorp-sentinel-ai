import {
  fireEvent,
  render,
  screen,
} from "@testing-library/react";
import {
  MemoryRouter,
  Route,
  Routes,
} from "react-router";
import {
  describe,
  expect,
  it,
  vi,
} from "vitest";

import FraudAlertCenterPage from "../pages/FraudAlertCenterPage";

const {
  selectedAlert,
  updateStatus,
} = vi.hoisted(() => ({
  selectedAlert: {
    id: 17,
    transaction_id: "TX-17",
    fraud_probability: 0.97,
    severity: "critical",
    risk_band: "critical",
    alert_status: "unread",
    created_at: "2026-07-28T08:00:00Z",
  },
  updateStatus: vi.fn(),
}));

vi.mock("../hooks/useAlertCenter", () => ({
  useAlertCenter: () => ({
    visibleAlerts: [selectedAlert],
    selectedAlert,
    filters: {
      query: "",
      severity: "",
      status: "",
      analyst: "",
      minimumProbability: 0,
    },
    sort: {
      field: "priority",
      direction: "desc",
    },
    summary: {
      total: 1,
      unread: 1,
      acknowledged: 0,
      investigating: 0,
      resolved: 0,
      critical: 1,
      high: 0,
      medium: 0,
      low: 0,
    },
    loading: false,
    error: null,
    loadAlerts: vi.fn().mockResolvedValue([]),
    setSelectedAlert: vi.fn(),
    updateStatus,
    updateFilters: vi.fn(),
    clearFilters: vi.fn(),
    setSort: vi.fn(),
  }),
}));

function renderAlertRoutes() {
  return render(
    <MemoryRouter initialEntries={["/fraud/alerts"]}>
      <Routes>
        <Route
          path="/fraud/alerts"
          element={<FraudAlertCenterPage />}
        />
        <Route
          path="/fraud/investigations"
          element={<h1>Investigation destination</h1>}
        />
        <Route
          path="/fraud/explainability"
          element={<h1>Explainability destination</h1>}
        />
        <Route
          path="/fraud/transactions"
          element={<h1>Transaction destination</h1>}
        />
      </Routes>
    </MemoryRouter>,
  );
}

describe("FraudAlertCenterPage", () => {
  it("renders the alert center and notification toolbar", () => {
    renderAlertRoutes();

    expect(
      screen.getByRole("heading", {
        name: /Fraud Alert Center/i,
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", {
        name: /Fraud alerts/i,
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Refreshes every 30 seconds/i),
    ).toBeInTheDocument();
  });

  it("routes the selected score to investigations", () => {
    renderAlertRoutes();

    fireEvent.click(
      screen.getByRole("button", {
        name: "Investigate",
      }),
    );

    expect(
      screen.getByRole("heading", {
        name: "Investigation destination",
      }),
    ).toBeInTheDocument();
    expect(updateStatus).toHaveBeenCalledWith(
      17,
      "investigating",
      null,
    );
  });

  it("routes the selected score to explainability", () => {
    renderAlertRoutes();

    fireEvent.click(
      screen.getByRole("button", {
        name: "View explanation",
      }),
    );

    expect(
      screen.getByRole("heading", {
        name: "Explainability destination",
      }),
    ).toBeInTheDocument();
  });

  it("routes the selected score to transaction detail", () => {
    renderAlertRoutes();

    fireEvent.click(
      screen.getByRole("button", {
        name: "View transaction",
      }),
    );

    expect(
      screen.getByRole("heading", {
        name: "Transaction destination",
      }),
    ).toBeInTheDocument();
  });
});
