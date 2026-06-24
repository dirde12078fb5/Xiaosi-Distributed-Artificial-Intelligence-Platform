// 把 plugins/skills/ 复制进 plugins/openclaw/skills/

import { cpSync, existsSync, rmSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const pluginRoot = resolve(here, "..");
const src = resolve(pluginRoot, "../skills");
const dest = resolve(pluginRoot, "skills");

if (!existsSync(src)) {
  console.error(`sync-skills: source not found at ${src}`);
  process.exit(1);
}

rmSync(dest, { recursive: true, force: true });
cpSync(src, dest, { recursive: true });
console.log(`sync-skills: ${src} → ${dest}`);
