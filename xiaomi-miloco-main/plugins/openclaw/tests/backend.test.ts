import { describe, expect, it } from "vitest";
import { runShell } from "../src/utils/shell.js";

describe("runShell", () => {
  it("异步 spawn 回传 stdout/stderr/code", async () => {
    const result = await runShell("/bin/sh", [
      "-c",
      "echo hello; echo err 1>&2; exit 0",
    ]);
    expect(result.status).toBe(0);
    expect(result.stdout).toContain("hello");
    expect(result.stderr).toContain("err");
  });

  it("非零退出码正确回传", async () => {
    const result = await runShell("/bin/sh", ["-c", "exit 7"]);
    expect(result.status).toBe(7);
  });
});
