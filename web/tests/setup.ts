import { cleanup } from "@testing-library/react";
import { afterEach, beforeEach, vi } from "vitest";

beforeEach(() => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => {
      throw new Error("Tests must not reach the network. Use mockFetch.");
    }),
  );
});

afterEach(() => {
  cleanup();
});
