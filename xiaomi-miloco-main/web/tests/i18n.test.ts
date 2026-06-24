/**
 * i18n 资源不变量 —— 守两类静默 bug：
 *  1. zh/en key 不对齐：en 缺 key 会被 fallbackLng 回退成中文，英文模式露中文。
 *  2. 插值占位符不一致：zh 用 {{msg}}、en 误写 {{message}}，运行期插值静默失效。
 * 外加 i18n 接线 smoke：默认 zh、切 en 生效、能切回。
 */
import { describe, it, expect, afterAll } from "vitest";
import { readdirSync, readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import i18n from "@/i18n";

const localesDir = fileURLToPath(new URL("../src/i18n/locales/", import.meta.url));

function flat(obj: Record<string, unknown>, prefix = ""): Record<string, string> {
  const out: Record<string, string> = {};
  for (const [k, v] of Object.entries(obj)) {
    const nk = prefix ? `${prefix}.${k}` : k;
    if (v && typeof v === "object") Object.assign(out, flat(v as Record<string, unknown>, nk));
    else out[nk] = String(v);
  }
  return out;
}

function loadDomain(loc: "zh" | "en", file: string): Record<string, string> {
  return flat(JSON.parse(readFileSync(`${localesDir}${loc}/${file}`, "utf8")));
}

function placeholders(s: string): string[] {
  return [...s.matchAll(/\{\{\s*(\w+)\s*\}\}/g)].map((m) => m[1]).sort();
}

const domains = readdirSync(`${localesDir}zh`).filter((f) => f.endsWith(".json"));

describe("i18n 资源完整性", () => {
  it("zh/en 域文件一一对应", () => {
    expect(readdirSync(`${localesDir}en`).filter((f) => f.endsWith(".json")).sort()).toEqual(
      [...domains].sort(),
    );
  });

  describe.each(domains)("%s", (file) => {
    const zh = loadDomain("zh", file);
    const en = loadDomain("en", file);

    it("zh/en key 完全对齐(防 en 缺 key 回退露中文)", () => {
      expect(Object.keys(en).sort()).toEqual(Object.keys(zh).sort());
    });

    // time 域有意例外：日期里中文用 {{m}}(数字月)、英文用 {{mon}}(短月名),
    // relativeTime 同时传 m+mon 由各语言模板各取所需,故占位符不要求两语言一致。
    const SKIP_PLACEHOLDER = new Set(["time.json"]);
    it.skipIf(SKIP_PLACEHOLDER.has(file))(
      "每个 key 的插值占位符 {{x}} 两语言一致",
      () => {
        for (const k of Object.keys(zh)) {
          expect(placeholders(en[k] ?? "")).toEqual(placeholders(zh[k]));
        }
      },
    );
  });
});

describe("i18n 接线 smoke", () => {
  afterAll(async () => {
    await i18n.changeLanguage("zh");
  });

  it("默认 zh,glob 合并后取词正常", () => {
    expect(i18n.language).toBe("zh");
    expect(i18n.t("nav.home")).toBe("概览");
  });

  it("切 en 后取到英文", async () => {
    await i18n.changeLanguage("en");
    expect(i18n.t("nav.home")).toBe("Overview");
  });

  it("未知 key 回退为 key 本身(不抛错)", () => {
    expect(i18n.t("nav.__missing__")).toBe("nav.__missing__");
  });
});
