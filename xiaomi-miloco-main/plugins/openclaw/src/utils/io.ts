import { randomBytes } from "node:crypto";
import {
  appendFileSync,
  mkdirSync,
  readFileSync,
  renameSync,
  unlinkSync,
  writeFileSync,
} from "node:fs";
import { appendFile, mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname } from "node:path";

export async function readTextFile(path: string): Promise<string> {
  return await readFile(path, "utf8");
}

export async function writeTextFile(path: string, text: string): Promise<void> {
  await mkdir(dirname(path), { recursive: true });
  await writeFile(path, text, "utf8");
}

export async function readJsonFile<T>(path: string): Promise<T | undefined> {
  try {
    const raw = await readTextFile(path);
    return JSON.parse(raw) as T;
  } catch {
    return undefined;
  }
}

export async function writeJsonFile(
  path: string,
  value: unknown,
  options?: { pretty?: boolean },
): Promise<void> {
  const text = options?.pretty
    ? `${JSON.stringify(value, null, 2)}\n`
    : JSON.stringify(value);
  await writeTextFile(path, text);
}

export async function appendTextLine(
  path: string,
  line: string,
): Promise<void> {
  await mkdir(dirname(path), { recursive: true });
  const normalized = line.endsWith("\n") ? line : `${line}\n`;
  await appendFile(path, normalized, "utf8");
}

export async function appendJSONLine(
  path: string,
  value: unknown,
): Promise<void> {
  await appendTextLine(path, JSON.stringify(value));
}

export function readTextFileSync(path: string): string {
  return readFileSync(path, "utf8");
}

export function writeTextFileSync(path: string, text: string): void {
  // Atomic write: 先写到同目录临时文件，再 rename 覆盖目标路径；
  mkdirSync(dirname(path), { recursive: true });
  const tmp = `${path}.tmp-${process.pid}-${randomBytes(6).toString("hex")}`;
  try {
    writeFileSync(tmp, text, "utf8");
    renameSync(tmp, path);
  } catch (err) {
    try {
      unlinkSync(tmp);
    } catch {
      /* best-effort cleanup */
    }
    throw err;
  }
}

export function readJsonFileSync<T>(path: string): T | undefined {
  try {
    const raw = readTextFileSync(path);
    return JSON.parse(raw) as T;
  } catch {
    return undefined;
  }
}

export function writeJsonFileSync(
  path: string,
  value: unknown,
  options?: { pretty?: boolean },
): void {
  const text = options?.pretty
    ? `${JSON.stringify(value, null, 2)}\n`
    : JSON.stringify(value);
  writeTextFileSync(path, text);
}

export function appendTextLineSync(path: string, line: string): void {
  mkdirSync(dirname(path), { recursive: true });
  const normalized = line.endsWith("\n") ? line : `${line}\n`;
  appendFileSync(path, normalized, "utf8");
}

export function appendJSONLineSync(path: string, value: unknown): void {
  appendTextLineSync(path, JSON.stringify(value));
}
