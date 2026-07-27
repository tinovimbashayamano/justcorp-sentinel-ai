import {
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";

import {
  getFraudCase,
  listFraudCases,
  updateFraudCase,
} from "../fraudCases";
import { httpClient } from "../httpClient";

vi.mock("../httpClient", () => ({
  httpClient: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
  },
}));

describe("fraud case API", () => {
  beforeEach(() => vi.clearAllMocks());

  it("lists cases with a limit", async () => {
    httpClient.get.mockResolvedValue({ data: [] });

    await listFraudCases({ limit: 25 });

    expect(httpClient.get).toHaveBeenCalledWith(
      "/api/v1/fraud/cases",
      { params: { limit: 25 } },
    );
  });

  it("gets one case", async () => {
    httpClient.get.mockResolvedValue({
      data: { id: 2 },
    });

    const result = await getFraudCase(2);

    expect(result.id).toBe(2);
  });

  it("updates one case", async () => {
    httpClient.patch.mockResolvedValue({
      data: {
        id: 2,
        case_status: "closed",
      },
    });

    await updateFraudCase(2, {
      case_status: "closed",
    });

    expect(httpClient.patch).toHaveBeenCalledWith(
      "/api/v1/fraud/cases/2",
      { case_status: "closed" },
    );
  });
});
