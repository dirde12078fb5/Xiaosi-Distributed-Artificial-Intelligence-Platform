import { describe, it, expect, beforeAll, afterAll } from "vitest";
import i18n from "@/i18n";
import { relativeTime, smartTimeParts } from "@/lib/relativeTime";

// 固定一个 "现在" 锚点：2026-05-25 (周一) 14:30:00 本地时区
const NOW = new Date(2026, 4, 25, 14, 30, 0); // month 是 0-indexed → 4 = 5月

describe("relativeTime — 7 个分支 + 边界(刚刚 / 分钟前 / 小时前 / 昨天 / M月D日 / YYYY 年 M月D日 / iso 边界)", () => {
  it("< 1 分钟 → '刚刚'", () => {
    const t = new Date(NOW.getTime() - 30 * 1000).toISOString();
    expect(relativeTime(t, NOW)).toBe("刚刚");
  });

  it("正好 0 分钟 → '刚刚'", () => {
    expect(relativeTime(NOW.toISOString(), NOW)).toBe("刚刚");
  });

  it("< 60 分钟 → 'X 分钟前'", () => {
    const t = new Date(NOW.getTime() - 15 * 60 * 1000).toISOString();
    expect(relativeTime(t, NOW)).toBe("15 分钟前");
  });

  it("59 分钟 → '59 分钟前'（边界）", () => {
    const t = new Date(NOW.getTime() - 59 * 60 * 1000).toISOString();
    expect(relativeTime(t, NOW)).toBe("59 分钟前");
  });

  it("60 分钟（同日）→ 'HH:MM'", () => {
    const t = new Date(NOW.getTime() - 60 * 60 * 1000); // 13:30
    expect(relativeTime(t.toISOString(), NOW)).toBe("13:30");
  });

  it("今日凌晨 02:05 → '02:05'（同日内更早时刻）", () => {
    const t = new Date(2026, 4, 25, 2, 5, 0);
    expect(relativeTime(t.toISOString(), NOW)).toBe("02:05");
  });

  it("昨天 23:50 → '昨天 23:50'", () => {
    const t = new Date(2026, 4, 24, 23, 50, 0);
    expect(relativeTime(t.toISOString(), NOW)).toBe("昨天 23:50");
  });

  it("跨午夜：now=00:01，input=昨天 23:50（< 60min 但跨日）→ '11 分钟前'", () => {
    // 这是分支语义自检：if diffMin < 60 优先级 > 昨天判断
    const earlyMorning = new Date(2026, 4, 25, 0, 1, 0);
    const yesterdayLate = new Date(2026, 4, 24, 23, 50, 0);
    expect(relativeTime(yesterdayLate.toISOString(), earlyMorning)).toBe(
      "11 分钟前",
    );
  });

  it("3 天前 → 'M 月 D 日'", () => {
    const t = new Date(2026, 4, 22, 10, 0, 0);
    expect(relativeTime(t.toISOString(), NOW)).toBe("5 月 22 日");
  });

  it("跨年(2025-12-31 vs now=2026-05-25)→ '2025 年 12 月 31 日'", () => {
    const t = new Date(2025, 11, 31, 10, 0, 0);
    expect(relativeTime(t.toISOString(), NOW)).toBe("2025 年 12 月 31 日");
  });

  it("接受带 offset 的 ISO 8601（contract 与 perception_log.t 一致）", () => {
    // 契约:relativeTime 能正确解析带时区 offset 的 ISO(perception_log.t 形如
    // 2026-05-25T14:30:00+08:00)。用 NOW 自身的 toISOString()(永远是 UTC Z 形式)
    // 喂回去——它指向跟 NOW 完全相同的瞬间,无论 CI runner 在哪个时区都应判"刚刚",
    // 不再硬编码 +08:00(原写法只在运行时区恰好 +08:00 时通过,UTC runner 会红)。
    const tzIso = NOW.toISOString();
    const result = relativeTime(tzIso, NOW);
    expect(["刚刚", "0 分钟前"]).toContain(result);
  });
});

describe("smartTimeParts — 3 分支(今天/昨天/YYYY/MM/DD)+ 边界", () => {
  // ActivityFeed 左栏 TimeLabel 唯一调用方;简化后只有 3 分支,守住边界防回归.
  // 原 5 分支版本有"周X" / "MM-DD" 分支,新版统一 YYYY/MM/DD 跨日格式.

  it("今天 → date='今天'", () => {
    expect(smartTimeParts(new Date(2026, 4, 25, 8, 0, 0).getTime(), NOW)).toEqual({
      time: "08:00:00",
      date: "今天",
    });
  });

  it("今天 23:59:59 → 仍是'今天'(同日内最晚边界)", () => {
    expect(
      smartTimeParts(new Date(2026, 4, 25, 23, 59, 59).getTime(), NOW),
    ).toEqual({ time: "23:59:59", date: "今天" });
  });

  it("昨天 → date='昨天'", () => {
    expect(
      smartTimeParts(new Date(2026, 4, 24, 23, 50, 0).getTime(), NOW),
    ).toEqual({ time: "23:50:00", date: "昨天" });
  });

  it("昨天 00:00:00 → 仍是'昨天'(整日边界)", () => {
    expect(
      smartTimeParts(new Date(2026, 4, 24, 0, 0, 0).getTime(), NOW),
    ).toEqual({ time: "00:00:00", date: "昨天" });
  });

  it("3 天前 → YYYY/MM/DD(不再显示'周X')", () => {
    expect(
      smartTimeParts(new Date(2026, 4, 22, 10, 0, 0).getTime(), NOW),
    ).toEqual({ time: "10:00:00", date: "2026/05/22" });
  });

  it("同年 1 月初 → YYYY/MM/DD(月份补零)", () => {
    expect(smartTimeParts(new Date(2026, 0, 5, 9, 0, 0).getTime(), NOW)).toEqual({
      time: "09:00:00",
      date: "2026/01/05",
    });
  });

  it("跨年 → YYYY/MM/DD", () => {
    expect(
      smartTimeParts(new Date(2025, 11, 31, 10, 0, 0).getTime(), NOW),
    ).toEqual({ time: "10:00:00", date: "2025/12/31" });
  });

  it("前天(2 天前)→ 也走 YYYY/MM/DD 分支(确认'昨天'不会被误延伸)", () => {
    expect(
      smartTimeParts(new Date(2026, 4, 23, 12, 0, 0).getTime(), NOW),
    ).toEqual({ time: "12:00:00", date: "2026/05/23" });
  });
});

// 英文分支：i18n.language="en" 时走 time.* 的英文模板。结束后必须还原 zh,
// 否则污染同文件后续(以及 i18n 单例)；时间数字部分(HH:MM / YYYY/MM/DD)语言无关不变。
describe("relativeTime / smartTimeParts — 英文分支", () => {
  beforeAll(async () => {
    await i18n.changeLanguage("en");
  });
  afterAll(async () => {
    await i18n.changeLanguage("zh");
  });

  it("< 1 分钟 → 'just now'", () => {
    const t = new Date(NOW.getTime() - 30 * 1000).toISOString();
    expect(relativeTime(t, NOW)).toBe("just now");
  });

  it("< 60 分钟 → 'N min ago'", () => {
    const t = new Date(NOW.getTime() - 15 * 60 * 1000).toISOString();
    expect(relativeTime(t, NOW)).toBe("15 min ago");
  });

  it("同日 → 'HH:MM'(纯时间,不随语言变)", () => {
    const t = new Date(NOW.getTime() - 60 * 60 * 1000); // 13:30
    expect(relativeTime(t.toISOString(), NOW)).toBe("13:30");
  });

  it("昨天 → 'Yesterday HH:MM'", () => {
    const t = new Date(2026, 4, 24, 23, 50, 0);
    expect(relativeTime(t.toISOString(), NOW)).toBe("Yesterday 23:50");
  });

  it("同年更早 → 'Mon D'(短月名走 Intl)", () => {
    const t = new Date(2026, 4, 22, 10, 0, 0);
    expect(relativeTime(t.toISOString(), NOW)).toBe("May 22");
  });

  it("跨年 → 'Mon D, YYYY'", () => {
    const t = new Date(2025, 11, 31, 10, 0, 0);
    expect(relativeTime(t.toISOString(), NOW)).toBe("Dec 31, 2025");
  });

  it("smartTimeParts 今天/昨天 → 'Today'/'Yesterday'", () => {
    expect(
      smartTimeParts(new Date(2026, 4, 25, 8, 0, 0).getTime(), NOW),
    ).toEqual({ time: "08:00:00", date: "Today" });
    expect(
      smartTimeParts(new Date(2026, 4, 24, 23, 50, 0).getTime(), NOW),
    ).toEqual({ time: "23:50:00", date: "Yesterday" });
  });

  it("smartTimeParts 跨日 → YYYY/MM/DD(数字格式不随语言变)", () => {
    expect(
      smartTimeParts(new Date(2026, 4, 22, 10, 0, 0).getTime(), NOW),
    ).toEqual({ time: "10:00:00", date: "2026/05/22" });
  });
});


