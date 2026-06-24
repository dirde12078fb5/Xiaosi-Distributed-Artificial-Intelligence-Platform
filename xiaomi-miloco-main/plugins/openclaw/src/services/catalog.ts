import fs from "node:fs";
import path from "node:path";
import { milocoHome } from "../miloco/paths.js";
import { logger } from "../utils/logger.js";
import { runShell } from "../utils/shell.js";

/**
 * Device catalog injection (spec-injection-plan §5.4).
 *
 * 在 before_prompt_build 钩子里跑 ``miloco-cli device catalog`` 生成目录文本。
 * CLI 内部每次都调后端 ``GET /api/miot/device_history`` 拿最新 LRU snapshot
 * 并读本地 home_info.json，所以重跑就能反映用户最近的控制行为。
 *
 * 5 秒节流：只防同一对话片段里 hook 被多次调用的 spam（异步 spawn 不阻塞事件
 * 循环，但短期 spam 没意义）。**不**把 home_info.json mtime 作为缓存命中条件——LRU
 * 变化在控制路径写入后端 SQLite，不会改 home_info.json mtime，用 mtime 等同
 * 判断会把 LRU 永远卡在缓存里，导致 miloco-cli device catalog 直跑的输出与
 * agent 注入的 catalog 不一致。
 *
 * 调 CLI 失败（未安装 / 后端未起 / spec 未填）时沿用旧缓存或返回空字符串，
 * 让 prompt 不带目录工作（agent 走 ``device list``+``device spec`` fallback）。
 */

// 与 cli/src/miloco_cli/config.py:miloco_home() 保持同款解析（$MILOCO_HOME 优先，
// 否则落回 ~/.openclaw/miloco）。两端用不同的 home 路径会让 mtime 失效逻辑读到
// 错误文件。
const HOME_INFO_PATH = path.join(milocoHome(), "home_info.json");

let cached: { text: string; generatedAt: number } | null = null;
const REGEN_THROTTLE_MS = 5_000; // 防抖：CLI 调用不应被 spam

function readHomeInfoMtime(): number {
  try {
    return fs.statSync(HOME_INFO_PATH).mtimeMs;
  } catch {
    return 0;
  }
}

async function runCliCatalog(): Promise<string | null> {
  const result = await runShell("miloco-cli", ["device", "catalog"], {
    // 后端慢（如批量 parse spec）会让 CLI 内部 httpx 等到 30s 超时。
    // 10s 上限到点 SIGTERM，runCliCatalog 返回 null → getCatalog 沿用旧缓存。
    timeout: 10_000,
  });
  if (result?.error) {
    logger.warn(
      `miloco-cli device catalog spawn failed: ${result.error.message}`,
    );
    return null;
  }
  // timeout 触发时 result.signal === "SIGTERM" 且 status === null
  if (result.signal) {
    logger.warn(
      `miloco-cli device catalog killed by ${result.signal} (likely 10s timeout)`,
    );
    return null;
  }
  if (result.status !== 0) {
    const stderr =
      (result.stderr ?? "").toString?.() ?? String(result.stderr ?? "");
    logger.warn(
      `miloco-cli device catalog exited ${result.status}: ${stderr.slice(0, 200)}`,
    );
    return null;
  }
  const stdout =
    (result.stdout ?? "").toString?.() ?? String(result.stdout ?? "");
  return stdout || null;
}

/**
 * 拿到当前缓存中的目录文本，必要时刷新。失败返回空字符串。
 */
export async function getCatalog(): Promise<string> {
  const now = Date.now();

  // 节流：5 秒内已经生成过 → 直接复用，避免同一对话片段里 hook 被多次触发
  // 时连续跑 CLI。超过 5 秒一律重跑——CLI 内部会拉最新 LRU + home_info。
  if (cached && now - cached.generatedAt < REGEN_THROTTLE_MS) {
    return cached.text;
  }

  const text = await runCliCatalog();
  if (text == null) {
    // 生成失败 → 沿用旧缓存（如果有），否则空字符串
    return cached?.text ?? "";
  }
  cached = { text, generatedAt: now };
  logger.info(
    `device catalog refreshed (${text.length} chars, home_info mtime=${readHomeInfoMtime()})`,
  );
  return text;
}

/**
 * 仅为测试 / hot-reload 之用：手动清缓存。
 */
export function _resetCatalogCache(): void {
  cached = null;
}
