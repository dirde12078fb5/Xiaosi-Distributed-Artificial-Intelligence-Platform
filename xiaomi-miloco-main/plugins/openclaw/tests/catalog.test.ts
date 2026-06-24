import { beforeEach, describe, expect, it, vi } from "vitest";

const { runShellMock } = vi.hoisted(() => ({ runShellMock: vi.fn() }));

vi.mock("../src/utils/shell.js", () => ({
  runShell: runShellMock,
}));
vi.mock("node:fs", () => ({
  default: { statSync: vi.fn() },
  statSync: vi.fn(),
}));
vi.mock("../src/utils/logger.js", () => ({
  logger: { info: vi.fn(), warn: vi.fn(), error: vi.fn(), debug: vi.fn() },
}));

import fs from "node:fs";
import { _resetCatalogCache, getCatalog } from "../src/services/catalog.js";

describe("getCatalog", () => {
  beforeEach(() => {
    _resetCatalogCache();
    vi.clearAllMocks();
  });

  it("returns CLI stdout on first call", async () => {
    (fs.statSync as any).mockReturnValue({ mtimeMs: 1000 });
    runShellMock.mockResolvedValue({
      status: 0,
      stdout: "# devices catalog\nfoo|bar|c|d|online\n",
      stderr: "",
      signal: null,
      error: null,
    });
    expect(await getCatalog()).toContain("# devices catalog");
    expect(runShellMock).toHaveBeenCalledWith(
      "miloco-cli",
      ["device", "catalog"],
      expect.any(Object),
    );
  });

  it("uses cache within throttle window (5s)", async () => {
    (fs.statSync as any).mockReturnValue({ mtimeMs: 1000 });
    runShellMock.mockResolvedValue({
      status: 0,
      stdout: "# devices catalog\n",
      stderr: "",
      signal: null,
      error: null,
    });
    await getCatalog();
    await getCatalog();
    expect(runShellMock).toHaveBeenCalledTimes(1);
  });

  it("regenerates after throttle window expires", async () => {
    runShellMock.mockResolvedValue({
      status: 0,
      stdout: "# v1\n",
      stderr: "",
      signal: null,
      error: null,
    });
    (fs.statSync as any).mockReturnValue({ mtimeMs: 1000 });
    await getCatalog();
    vi.useFakeTimers();
    vi.setSystemTime(new Date(Date.now() + 10_000));
    runShellMock.mockResolvedValue({
      status: 0,
      stdout: "# v2\n",
      stderr: "",
      signal: null,
      error: null,
    });
    const out = await getCatalog();
    vi.useRealTimers();
    expect(out).toContain("v2");
    expect(runShellMock).toHaveBeenCalledTimes(2);
  });

  it("regenerates after throttle even when home_info mtime unchanged (LRU update)", async () => {
    (fs.statSync as any).mockReturnValue({ mtimeMs: 1000 });
    runShellMock.mockResolvedValue({
      status: 0,
      stdout: "# before LRU touch\n",
      stderr: "",
      signal: null,
      error: null,
    });
    await getCatalog();
    vi.useFakeTimers();
    vi.setSystemTime(new Date(Date.now() + 10_000));
    runShellMock.mockResolvedValue({
      status: 0,
      stdout: "# after LRU touch\n",
      stderr: "",
      signal: null,
      error: null,
    });
    const out = await getCatalog();
    vi.useRealTimers();
    expect(out).toContain("after LRU touch");
    expect(runShellMock).toHaveBeenCalledTimes(2);
  });

  it("falls back to old cache on CLI failure", async () => {
    (fs.statSync as any).mockReturnValue({ mtimeMs: 1000 });
    runShellMock.mockResolvedValue({
      status: 0,
      stdout: "# good\n",
      stderr: "",
      signal: null,
      error: null,
    });
    expect(await getCatalog()).toContain("# good");
    vi.useFakeTimers();
    vi.setSystemTime(new Date(Date.now() + 10_000));
    runShellMock.mockResolvedValue({
      status: 1,
      stdout: "",
      stderr: "boom",
      signal: null,
      error: null,
    });
    const out = await getCatalog();
    vi.useRealTimers();
    expect(out).toContain("# good");
  });

  it("returns empty string when no cache and CLI fails", async () => {
    (fs.statSync as any).mockReturnValue({ mtimeMs: 1000 });
    runShellMock.mockResolvedValue({
      status: 127,
      stdout: "",
      stderr: "command not found",
      signal: null,
      error: null,
    });
    expect(await getCatalog()).toBe("");
  });
});
