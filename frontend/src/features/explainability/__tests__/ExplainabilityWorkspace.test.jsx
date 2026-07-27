import { render, screen } from "@testing-library/react";
import {
  describe,
  expect,
  it,
  vi,
} from "vitest";

import ExplainabilityWorkspace from "../pages/ExplainabilityWorkspace";

vi.mock(
  "../hooks/useExplainabilityWorkspace",
  () => ({
    useExplainabilityWorkspace: () => ({
      data: {
        health: {
          status: "ready",
          local_explainability: "ready",
          global_explainability: "ready",
        },
        local: null,
        waterfall: null,
        force: null,
        global: null,
        globalSummary: null,
      },
      loading: {},
      error: null,
      loadHealth: vi.fn(),
      loadGlobal: vi.fn(),
      explainTransaction: vi.fn(),
      exportReport: vi.fn(),
    }),
  }),
);

describe("ExplainabilityWorkspace", () => {
  it("renders the workspace", () => {
    render(<ExplainabilityWorkspace />);

    expect(
      screen.getByRole("heading", {
        name: /Explainability Investigation Workspace/i,
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Explainability ready/i),
    ).toBeInTheDocument();
  });
});
