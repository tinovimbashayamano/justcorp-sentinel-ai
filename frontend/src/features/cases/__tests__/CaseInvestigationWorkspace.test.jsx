import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import {
  describe,
  expect,
  it,
  vi,
} from "vitest";

import CaseInvestigationWorkspace from "../pages/CaseInvestigationWorkspace";

vi.mock(
  "../hooks/useCaseInvestigationWorkspace",
  () => ({
    useCaseInvestigationWorkspace: () => ({
      data: {
        cases: [],
        scores: [],
        selectedCase: null,
      },
      loading: {},
      error: null,
      selectedScore: null,
      loadWorkspace: vi.fn().mockResolvedValue({}),
      selectCase: vi.fn(),
      saveCase: vi.fn(),
    }),
  }),
);

describe("CaseInvestigationWorkspace", () => {
  it("renders the investigation workspace", () => {
    render(
      <MemoryRouter>
        <CaseInvestigationWorkspace />
      </MemoryRouter>,
    );

    expect(
      screen.getByRole("heading", {
        name: /Fraud Case Investigation Workspace/i,
      }),
    ).toBeInTheDocument();
  });
});
