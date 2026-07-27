import { describe, expect, it, vi } from "vitest";

import {
  base64ToBlob,
  createDataUrl,
} from "../utils/base64";

describe("base64 utilities", () => {
  it("creates a data URL", () => {
    expect(
      createDataUrl("YWJj", "text/plain"),
    ).toBe("data:text/plain;base64,YWJj");
  });

  it("creates a blob", () => {
    vi.stubGlobal("atob", (value) =>
      Buffer.from(value, "base64").toString("binary"),
    );

    const blob = base64ToBlob("YWJj", "text/plain");

    expect(blob.type).toBe("text/plain");
    expect(blob.size).toBe(3);
  });
});
