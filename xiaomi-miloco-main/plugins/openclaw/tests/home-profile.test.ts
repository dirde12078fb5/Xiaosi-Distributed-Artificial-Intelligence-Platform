import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import {
  homeProfilePath,
  loadHomeProfile,
  readFileSafe,
} from "../src/home-profile/helpers.js";
import { buildPendingSuggestionBlock } from "../src/home-profile/injection.js";

// 家庭档案逻辑已下沉 backend（miloco-cli home-profile）；
// plugin 侧只保留 canonical profile.md 的本地只读 + system prompt 注入。

let tmpHome: string;
const prevEnv = process.env.MILOCO_HOME;

beforeEach(() => {
  tmpHome = mkdtempSync(path.join(tmpdir(), "miloco-home-"));
  process.env.MILOCO_HOME = tmpHome;
});

afterEach(() => {
  if (prevEnv === undefined) delete process.env.MILOCO_HOME;
  else process.env.MILOCO_HOME = prevEnv;
  rmSync(tmpHome, { recursive: true, force: true });
});

function writeProfile(content: string): string {
  const p = homeProfilePath();
  mkdirSync(path.dirname(p), { recursive: true });
  writeFileSync(p, content, "utf8");
  return p;
}

describe("homeProfilePath", () => {
  it("指向 $MILOCO_HOME/home-profile/profile.md", () => {
    expect(homeProfilePath()).toBe(
      path.join(tmpHome, "home-profile", "profile.md"),
    );
  });

  it("跟随 MILOCO_HOME 环境变量变化", () => {
    const other = mkdtempSync(path.join(tmpdir(), "miloco-other-"));
    process.env.MILOCO_HOME = other;
    try {
      expect(homeProfilePath()).toBe(
        path.join(other, "home-profile", "profile.md"),
      );
    } finally {
      rmSync(other, { recursive: true, force: true });
    }
  });
});

describe("readFileSafe", () => {
  it("存在文件返回内容", () => {
    const p = writeProfile("hello world");
    expect(readFileSafe(p)).toBe("hello world");
  });

  it("缺失文件返回空串（不抛错）", () => {
    expect(readFileSafe(path.join(tmpHome, "nope.md"))).toBe("");
  });
});

describe("loadHomeProfile", () => {
  it("有 profile.md 时返回其内容", () => {
    writeProfile("### 爸爸\n- 喜欢 24°C 制冷");
    expect(loadHomeProfile()).toBe("### 爸爸\n- 喜欢 24°C 制冷");
  });

  it("缺失时返回占位文案（不触发 render）", () => {
    expect(loadHomeProfile()).toBe("(暂无内容)");
  });

  it("空文件也返回占位文案", () => {
    writeProfile("");
    expect(loadHomeProfile()).toBe("(暂无内容)");
  });
});

describe("buildPendingSuggestionBlock", () => {
  it("无未决习惯建议时返回空串（正常日子静默）", () => {
    expect(buildPendingSuggestionBlock()).toBe("");
  });
});
