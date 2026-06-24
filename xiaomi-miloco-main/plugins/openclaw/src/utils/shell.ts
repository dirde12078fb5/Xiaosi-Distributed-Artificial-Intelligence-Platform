import child_process, { type SpawnOptions } from "node:child_process";

export interface ShellResult {
  status: number | null;
  stdout: string;
  stderr: string;
  signal: NodeJS.Signals | null;
  error: Error | null;
}

export function runShell(
  command: string,
  args: string[],
  options?: SpawnOptions,
): Promise<ShellResult> {
  return new Promise((resolve) => {
    const child = child_process["spawn"](command, args, {
      stdio: ["pipe", "pipe", "pipe"],
      ...options,
      env: { ...process.env, ...(options?.env ?? {}) },
    });
    const stdoutChunks: Buffer[] = [];
    const stderrChunks: Buffer[] = [];

    child.stdout?.on("data", (chunk: Buffer) => stdoutChunks.push(chunk));
    child.stderr?.on("data", (chunk: Buffer) => stderrChunks.push(chunk));

    child.on("error", (error) =>
      resolve({
        status: 1,
        stdout: "",
        stderr: "",
        signal: null,
        error: error,
      }),
    );
    child.on("close", (code, signal) => {
      resolve({
        status: code,
        stdout: Buffer.concat(stdoutChunks).toString("utf-8"),
        stderr: Buffer.concat(stderrChunks).toString("utf-8"),
        signal,
        error: null,
      });
    });
  });
}
