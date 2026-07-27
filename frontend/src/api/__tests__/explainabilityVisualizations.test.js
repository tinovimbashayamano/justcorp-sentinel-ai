import {
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";

import {
  exportInvestigationReport,
  getGlobalVisualization,
  getLocalVisualization,
} from "../explainabilityVisualizations";
import { httpClient } from "../httpClient";

vi.mock("../httpClient", () => ({
  httpClient: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

describe("explainability visualization API", () => {
  beforeEach(() => vi.clearAllMocks());

  it("requests local data", async () => {
    httpClient.post.mockResolvedValue({
      data: { transaction_id: "TX-1" },
    });

    const result = await getLocalVisualization({
      transaction_id: "TX-1",
      features: {},
      top_features: 10,
    });

    expect(httpClient.post).toHaveBeenCalledWith(
      "/api/v1/explainability-visualizations/local/data",
      expect.objectContaining({
        transaction_id: "TX-1",
      }),
    );
    expect(result.transaction_id).toBe("TX-1");
  });

  it("passes a global limit", async () => {
    httpClient.get.mockResolvedValue({
      data: { features: [] },
    });

    await getGlobalVisualization(12);

    expect(httpClient.get).toHaveBeenCalledWith(
      "/api/v1/explainability-visualizations/global/data",
      { params: { limit: 12 } },
    );
  });

  it("rejects unsupported report formats", async () => {
    await expect(
      exportInvestigationReport("docx", {}),
    ).rejects.toThrow("Report format");
  });
});
