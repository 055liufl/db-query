import { afterEach, describe, expect, it, vi } from "vitest";

import { apiRoot } from "./api";

describe("apiRoot", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
    vi.stubGlobal("window", undefined);
  });

  it("uses VITE_API_BASE_URL when set", () => {
    vi.stubEnv("VITE_API_BASE_URL", "http://example.com:9000/");
    expect(apiRoot()).toBe("http://example.com:9000");
  });

  it("uses window location when in browser and env unset", () => {
    vi.stubEnv("VITE_API_BASE_URL", "");
    vi.stubGlobal("window", {
      location: { protocol: "http:", hostname: "192.168.1.5", port: "3000" },
    });
    expect(apiRoot()).toBe("http://192.168.1.5:8000");
  });

  it("falls back to 127.0.0.1 when not in browser", () => {
    vi.stubEnv("VITE_API_BASE_URL", "");
    expect(apiRoot()).toBe("http://127.0.0.1:8000");
  });
});
