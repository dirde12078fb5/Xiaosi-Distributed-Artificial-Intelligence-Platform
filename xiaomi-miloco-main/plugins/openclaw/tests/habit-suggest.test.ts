import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { habitSuggestionsPath } from "../src/home-profile/helpers.js";
import {
  applyHabitAction,
  loadOpenQuestions,
  localDateKey,
} from "../src/home-profile/suggestions.js";

let tmpHome: string;
const prevHomeEnv = process.env.MILOCO_HOME;
const prevTzEnv = process.env.MILOCO_TIMEZONE;

beforeEach(() => {
  tmpHome = mkdtempSync(path.join(tmpdir(), "miloco-suggest-"));
  process.env.MILOCO_HOME = tmpHome;
  // 所有 fixture 的 ISO 字符串(D6_10 / D6_23 / D6_0730 等)都用 +08:00 后缀,
  // 测试预期(如 localDateKey 返回 "2026-06-06")只在 Asia/Shanghai 部署下成立。
  // 不锁 env 则随 CI 容器 / 开发机系统时区飘。
  process.env.MILOCO_TIMEZONE = "Asia/Shanghai";
});

afterEach(() => {
  if (prevHomeEnv === undefined) delete process.env.MILOCO_HOME;
  else process.env.MILOCO_HOME = prevHomeEnv;
  if (prevTzEnv === undefined) delete process.env.MILOCO_TIMEZONE;
  else process.env.MILOCO_TIMEZONE = prevTzEnv;
  rmSync(tmpHome, { recursive: true, force: true });
});

// 固定一组测试用 now（Asia/Shanghai +08:00）
const D6_10 = "2026-06-06T10:00:00+08:00";
const D6_23 = "2026-06-06T23:50:00+08:00";
const D6_0730 = "2026-06-06T07:30:00+08:00"; // UTC 仍是 06-05，用于跨时区日界校验
const D7_10 = "2026-06-07T10:00:00+08:00";
const D14_10 = "2026-06-14T10:00:00+08:00"; // D6 之后第 8 天

// 身份（key）由 agent 自己起；测试里直接传入。
const record = (key: string, habit: string, suggestion: string, now = D6_10) =>
  applyHabitAction(
    { action: "record", key, subject: "shared", habit, suggestion },
    now,
  );
const list = (now = D6_10) => applyHabitAction({ action: "list" }, now);

describe("路径辅助：habitSuggestionsPath", () => {
  it("指向 $MILOCO_HOME/home-profile/task-suggestions.json", () => {
    expect(habitSuggestionsPath()).toBe(
      path.join(tmpHome, "home-profile", "task-suggestions.json"),
    );
  });
});

describe("localDateKey", () => {
  it("按部署时区取日历日，跨 UTC 日界仍同日", () => {
    // 07:30+08:00 在 UTC 是前一天 23:30，但上海日历日应为 06-06
    expect(localDateKey(D6_0730)).toBe("2026-06-06");
    expect(localDateKey(D6_23)).toBe("2026-06-06");
  });
});

describe("record：按 agent 提供的 key 幂等去重 / 拒绝不复活", () => {
  it("首次 record 建 pending 并回显 key", async () => {
    const r = await record("wl_sleep_dim", "23点睡觉", "睡觉时把台灯调暗");
    expect(r.ok).toBe(true);
    expect(r.status).toBe("pending");
    expect(r.deduped).toBe(false);
    expect(r.key).toBe("wl_sleep_dim");
  });

  it("同一 key 重复 record（哪怕措辞不同）→ 去重，不新建副本", async () => {
    await record("wl_sleep_dim", "23点睡觉", "睡觉时把台灯调暗");
    const r2 = await record("wl_sleep_dim", "每晚23点入睡", "睡觉调暗灯");
    expect(r2.deduped).toBe(true);
    const l = await list();
    expect((l.counts as Record<string, number>).pending).toBe(1);
  });

  it("缺 key 或 habit/suggestion → ok:false", async () => {
    const noKey = await applyHabitAction(
      { action: "record", subject: "shared", habit: "x", suggestion: "y" },
      D6_10,
    );
    expect(noKey.ok).toBe(false);
    const noHabit = await applyHabitAction(
      { action: "record", key: "k1", suggestion: "y" },
      D6_10,
    );
    expect(noHabit.ok).toBe(false);
  });

  it("已拒绝的 key 再次 record → 返回 rejected，不复活成 pending", async () => {
    await record("wl_sleep_dim", "23点睡觉", "睡觉调暗灯");
    await applyHabitAction(
      { action: "mark_asked", key: "wl_sleep_dim" },
      D6_10,
    );
    await applyHabitAction(
      { action: "resolve", key: "wl_sleep_dim", outcome: "rejected" },
      D6_10,
    );

    const again = await record(
      "wl_sleep_dim",
      "每晚23点睡觉习惯",
      "睡觉调暗灯",
      D7_10,
    );
    expect(again.deduped).toBe(true);
    expect(again.status).toBe("rejected");
    const l = await list(D7_10);
    const counts = l.counts as Record<string, number>;
    expect(counts.rejected).toBe(1);
    expect(counts.pending ?? 0).toBe(0);
  });

  it("list 的 entries 暴露全部条目（含终态），供 agent 判重", async () => {
    await record("wl_sleep_dim", "23点睡觉", "睡觉调暗灯");
    await applyHabitAction(
      { action: "mark_asked", key: "wl_sleep_dim" },
      D6_10,
    );
    await applyHabitAction(
      { action: "resolve", key: "wl_sleep_dim", outcome: "rejected" },
      D6_10,
    );
    const l = await list(D6_10);
    const entries = l.entries as Array<{ key: string; status: string }>;
    expect(entries).toHaveLength(1);
    expect(entries[0]).toMatchObject({
      key: "wl_sleep_dim",
      status: "rejected",
    });
  });
});

describe("防骚扰闸门：can_ask_now / mark_asked", () => {
  it("空库可问；问出一条后被『已有待回应』挡住", async () => {
    await record("wl_sleep_dim", "23点睡觉", "睡觉调暗灯");
    await record("zx_whitenoise", "睡前听白噪音", "睡觉放白噪音");
    expect((await list()).can_ask_now).toBe(true);

    const ask = await applyHabitAction(
      { action: "mark_asked", key: "wl_sleep_dim" },
      D6_10,
    );
    expect(ask.ok).toBe(true);
    expect(ask.status).toBe("asked");

    // 已有待回应 → 第二条被工具拒绝
    expect((await list()).can_ask_now).toBe(false);
    const ask2 = await applyHabitAction(
      { action: "mark_asked", key: "zx_whitenoise" },
      D6_10,
    );
    expect(ask2.ok).toBe(false);
  });

  it("回应掉当天那条后，当天仍不再新推（每天至多 1 条）", async () => {
    await record("wl_sleep_dim", "23点睡觉", "睡觉调暗灯");
    await record("zx_whitenoise", "睡前听白噪音", "睡觉放白噪音");
    await applyHabitAction(
      { action: "mark_asked", key: "wl_sleep_dim" },
      D6_10,
    );
    await applyHabitAction(
      { action: "resolve", key: "wl_sleep_dim", outcome: "rejected" },
      D6_23,
    );

    // 同一上海日历日：已问过 → 仍不能问
    expect((await list(D6_23)).can_ask_now).toBe(false);
    const ask2 = await applyHabitAction(
      { action: "mark_asked", key: "zx_whitenoise" },
      D6_23,
    );
    expect(ask2.ok).toBe(false);

    // 次日：无待回应、未问过 → 可以问
    expect((await list(D7_10)).can_ask_now).toBe(true);
    const ask3 = await applyHabitAction(
      { action: "mark_asked", key: "zx_whitenoise" },
      D7_10,
    );
    expect(ask3.ok).toBe(true);
  });

  it("mark_asked 只接受 pending 状态", async () => {
    await record("wl_sleep_dim", "23点睡觉", "睡觉调暗灯");
    await applyHabitAction(
      { action: "mark_asked", key: "wl_sleep_dim" },
      D6_10,
    );
    // 已是 asked，再 mark 一次 → 拒绝
    const again = await applyHabitAction(
      { action: "mark_asked", key: "wl_sleep_dim" },
      D6_10,
    );
    expect(again.ok).toBe(false);
  });
});

describe("resolve 合法转移", () => {
  it("asked → accepted → created（回填 task_id）", async () => {
    await record("wl_gym", "傍晚健身", "健身时放运动歌单");
    await applyHabitAction({ action: "mark_asked", key: "wl_gym" }, D6_10);

    const acc = await applyHabitAction(
      { action: "resolve", key: "wl_gym", outcome: "accepted" },
      D6_10,
    );
    expect(acc.ok).toBe(true);
    expect(acc.status).toBe("accepted");

    const created = await applyHabitAction(
      {
        action: "resolve",
        key: "wl_gym",
        outcome: "created",
        task_id: "gym_music",
      },
      D6_10,
    );
    expect(created.ok).toBe(true);
    expect(created.status).toBe("created");
    expect(created.task_id).toBe("gym_music");
  });

  it("已建任务不能再被接受/拒绝", async () => {
    await record("wl_gym", "傍晚健身", "健身时放运动歌单");
    await applyHabitAction({ action: "mark_asked", key: "wl_gym" }, D6_10);
    await applyHabitAction(
      {
        action: "resolve",
        key: "wl_gym",
        outcome: "created",
        task_id: "gym_music",
      },
      D6_10,
    );
    const bad = await applyHabitAction(
      { action: "resolve", key: "wl_gym", outcome: "rejected" },
      D6_10,
    );
    expect(bad.ok).toBe(false);
  });

  it("未知 key → ok:false", async () => {
    const r = await applyHabitAction(
      { action: "resolve", key: "nope", outcome: "accepted" },
      D6_10,
    );
    expect(r.ok).toBe(false);
  });

  it("pending 直接 created 被拒（未询问过的条目不能凭空成已建）", async () => {
    await record("wl_gym", "傍晚健身", "健身时放运动歌单");
    const bad = await applyHabitAction(
      { action: "resolve", key: "wl_gym", outcome: "created", task_id: "x" },
      D6_10,
    );
    expect(bad.ok).toBe(false);
    expect(bad.status).toBe("pending");
  });

  it("asked 直接 created 可走（用户当轮接受并建好的快捷路径）", async () => {
    await record("wl_gym", "傍晚健身", "健身时放运动歌单");
    await applyHabitAction({ action: "mark_asked", key: "wl_gym" }, D6_10);
    const created = await applyHabitAction(
      { action: "resolve", key: "wl_gym", outcome: "created", task_id: "gym" },
      D6_10,
    );
    expect(created.ok).toBe(true);
    expect(created.status).toBe("created");
  });

  it("pending 直接 accepted 被拒（accepted 仅从 asked 流转）", async () => {
    await record("wl_gym", "傍晚健身", "健身时放运动歌单");
    const bad = await applyHabitAction(
      { action: "resolve", key: "wl_gym", outcome: "accepted" },
      D6_10,
    );
    expect(bad.ok).toBe(false);
    expect(bad.status).toBe("pending");
  });
});

describe("7 天过期与重新推荐", () => {
  it("asked 超 7 天无回应 → expired，释放待回应位", async () => {
    await record("wl_sleep_dim", "23点睡觉", "睡觉调暗灯");
    await applyHabitAction(
      { action: "mark_asked", key: "wl_sleep_dim" },
      D6_10,
    );

    const l = await list(D14_10); // 第 8 天：list 触发惰性过期
    const counts = l.counts as Record<string, number>;
    expect(counts.expired).toBe(1);
    expect(counts.asked ?? 0).toBe(0);
    expect(l.can_ask_now).toBe(true); // 待回应位已释放
  });

  it("过期未答复的条目，下次 record 复活为 pending 并可重新询问", async () => {
    await record("wl_sleep_dim", "23点睡觉", "睡觉调暗灯");
    await applyHabitAction(
      { action: "mark_asked", key: "wl_sleep_dim" },
      D6_10,
    );
    await list(D14_10); // 触发过期

    // 同 key 再 record → 复活为 pending（保留身份，不新建副本）
    const revived = await record(
      "wl_sleep_dim",
      "每晚23点睡觉",
      "睡觉调暗灯",
      D14_10,
    );
    expect(revived.status).toBe("pending");
    expect(revived.revived).toBe(true);
    const counts = (await list(D14_10)).counts as Record<string, number>;
    expect(counts.pending).toBe(1);
    expect(counts.expired ?? 0).toBe(0);

    // 复活后可再次询问
    const ask = await applyHabitAction(
      { action: "mark_asked", key: "wl_sleep_dim" },
      D14_10,
    );
    expect(ask.ok).toBe(true);
    expect(ask.status).toBe("asked");
  });

  it("accepted 超 7 天未建成 → expired（防 create-task 中途失败的永久 limbo），且可被重新推荐", async () => {
    // 模拟：用户同意（accepted）但 create-task 当轮反问/中断，始终没 resolve(created)
    await record("wl_gym", "傍晚健身", "健身时放运动歌单");
    await applyHabitAction({ action: "mark_asked", key: "wl_gym" }, D6_10);
    await applyHabitAction(
      { action: "resolve", key: "wl_gym", outcome: "accepted" },
      D6_10,
    );

    const l = await list(D14_10); // 第 8 天：accepted 被回收为 expired
    const counts = l.counts as Record<string, number>;
    expect(counts.expired).toBe(1);
    expect(counts.accepted ?? 0).toBe(0);
    expect(l.can_ask_now).toBe(true);

    // 同 key 再 record → 复活重推
    const revived = await record(
      "wl_gym",
      "傍晚健身",
      "健身时放运动歌单",
      D14_10,
    );
    expect(revived.status).toBe("pending");
    expect(revived.revived).toBe(true);
  });

  it("累计问满 3 次仍无回应 → 永久放弃，不再复活重推", async () => {
    const D22 = "2026-06-22T10:00:00+08:00";
    const D30 = "2026-06-30T10:00:00+08:00";
    await record("wl_sleep_dim", "23点睡觉", "睡觉调暗灯");

    // 第 1 次：问 → 过期 → 复活
    await applyHabitAction(
      { action: "mark_asked", key: "wl_sleep_dim" },
      D6_10,
    );
    let r = await record("wl_sleep_dim", "23点睡觉", "睡觉调暗灯", D14_10);
    expect(r.revived).toBe(true);
    // 第 2 次：问 → 过期 → 复活
    await applyHabitAction(
      { action: "mark_asked", key: "wl_sleep_dim" },
      D14_10,
    );
    r = await record("wl_sleep_dim", "23点睡觉", "睡觉调暗灯", D22);
    expect(r.revived).toBe(true);
    // 第 3 次：问 → 过期 → 已问满 3 次，放弃（不再复活）
    await applyHabitAction({ action: "mark_asked", key: "wl_sleep_dim" }, D22);
    r = await record("wl_sleep_dim", "23点睡觉", "睡觉调暗灯", D30);
    expect(r.revived).toBeUndefined();
    expect(r.status).toBe("expired");

    const counts = (await list(D30)).counts as Record<string, number>;
    expect(counts.expired).toBe(1);
    expect(counts.pending ?? 0).toBe(0);
  });
});

describe("loadOpenQuestions（injection 用）", () => {
  it("只返回未作废的 asked 条目", async () => {
    await record("wl_sleep_dim", "23点睡觉", "睡觉调暗灯");
    await applyHabitAction(
      { action: "mark_asked", key: "wl_sleep_dim" },
      D6_10,
    );
    expect(loadOpenQuestions(D6_23).length).toBe(1);
    expect(loadOpenQuestions(D14_10).length).toBe(0); // 已超 7 天
  });
});

describe("进程内互斥：并发写不丢条目", () => {
  it("并发 record 10 条不同 key → 全部落盘", async () => {
    const jobs = Array.from({ length: 10 }, (_, i) =>
      record(`habit_${i}`, `习惯编号${i}做某事`, `任务点子${i}`),
    );
    await Promise.all(jobs);
    const l = await list();
    expect((l.counts as Record<string, number>).pending).toBe(10);
  });
});

describe("item_id：追踪建议来源", () => {
  const view = (l: Record<string, unknown>, key: string) =>
    (l.entries as Array<{ key: string; item_id?: string }>).find(
      (e) => e.key === key,
    );

  it("record 带 item_id → list/view 能读回，建任务后随条目保留", async () => {
    await applyHabitAction(
      {
        action: "record",
        key: "wl_fitness",
        subject: "王磊",
        habit: "傍晚约19点健身",
        suggestion: "健身时自动放运动歌单",
        item_id: "p-abc123",
      },
      D6_10,
    );
    expect(view(await list(), "wl_fitness")?.item_id).toBe("p-abc123");

    await applyHabitAction({ action: "mark_asked", key: "wl_fitness" }, D6_10);
    await applyHabitAction(
      { action: "resolve", key: "wl_fitness", outcome: "created", task_id: "t1" },
      D6_10,
    );
    expect(view(await list(D7_10), "wl_fitness")?.item_id).toBe("p-abc123");
  });

  it("过期复活时刷新 item_id", async () => {
    await applyHabitAction(
      {
        action: "record",
        key: "wl_water",
        subject: "王磊",
        habit: "下午喝水",
        suggestion: "提醒喝水",
        item_id: "p-old",
      },
      D6_10,
    );
    await applyHabitAction({ action: "mark_asked", key: "wl_water" }, D6_10);
    // D14 已超 7 天 → asked 过期；同 key record 复活并刷新 item_id
    await applyHabitAction(
      {
        action: "record",
        key: "wl_water",
        subject: "王磊",
        habit: "下午喝水",
        suggestion: "提醒喝水",
        item_id: "p-new",
      },
      D14_10,
    );
    expect(view(await list(D14_10), "wl_water")?.item_id).toBe("p-new");
  });
});
