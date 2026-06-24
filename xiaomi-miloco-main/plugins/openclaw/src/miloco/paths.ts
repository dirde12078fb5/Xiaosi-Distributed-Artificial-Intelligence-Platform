/**
 * 解析 MILOCO_HOME 路径。
 *
 * 优先读 `MILOCO_HOME` 环境变量；未设置则落回 `~/.openclaw/miloco`。
 * 与后端 Python 侧 `miloco.utils.paths.miloco_home()` 与
 * CLI 侧 `miloco_cli.config.miloco_home()` 行为保持一致。
 */
import { homedir } from "node:os";
import path from "node:path";

/**
 * 返回 `$MILOCO_HOME`，未设置则使用 `~/.openclaw/miloco`。
 *
 * 每次调用都读取环境变量，便于测试用 `process.env.MILOCO_HOME` 临时注入。
 */
export function milocoHome(): string {
  const env = process.env.MILOCO_HOME;
  if (env && env.length > 0) {
    return env.startsWith("~") ? path.join(homedir(), env.slice(1)) : env;
  }
  return path.join(homedir(), ".openclaw", "miloco");
}

/**
 * 返回 `$MILOCO_HOME/config.json`（共享嵌套配置文件）。
 */
export function milocoConfigFile(): string {
  return path.join(milocoHome(), "config.json");
}
