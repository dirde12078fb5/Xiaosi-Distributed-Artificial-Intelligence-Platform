import { describe, it, expect } from "vitest";
import {
  BUCKET_MS,
  densifyByBucket,
  formatPerfTs,
  isPendingBucket,
  splitClosedPending,
} from "@/lib/perfBucket";

const HOUR = 60 * 60_000;

describe("isPendingBucket", () => {
  // 锚点:2026-05-28 10:42:00 (用户截图时刻)
  const NOW = new Date(2026, 4, 28, 10, 42, 0).getTime();

  it("1h bucket: 10:00 桶在 10:42 仍在累积 → pending", () => {
    const ts = new Date(2026, 4, 28, 10, 0, 0).getTime();
    expect(isPendingBucket(ts, "1h", NOW)).toBe(true);
  });

  it("1h bucket: 9:00 桶在 10:42 已结束 → 非 pending", () => {
    const ts = new Date(2026, 4, 28, 9, 0, 0).getTime();
    expect(isPendingBucket(ts, "1h", NOW)).toBe(false);
  });

  it("5m bucket: 10:40 桶在 10:42 仍在累积 → pending", () => {
    const ts = new Date(2026, 4, 28, 10, 40, 0).getTime();
    expect(isPendingBucket(ts, "5m", NOW)).toBe(true);
  });

  it("5m bucket: 10:35 桶在 10:42 已结束 → 非 pending", () => {
    const ts = new Date(2026, 4, 28, 10, 35, 0).getTime();
    expect(isPendingBucket(ts, "5m", NOW)).toBe(false);
  });

  it("桶起点 + bucket_ms 恰好等于 now → 非 pending (边界已结束)", () => {
    const ts = NOW - HOUR;
    expect(isPendingBucket(ts, "1h", NOW)).toBe(false);
  });

  it("BUCKET_MS 表跟后端 stats.py _BUCKET_MS 对齐", () => {
    expect(BUCKET_MS["5m"]).toBe(5 * 60_000);
    expect(BUCKET_MS["1h"]).toBe(60 * 60_000);
    expect(BUCKET_MS["1d"]).toBe(24 * 60 * 60_000);
  });
});

describe("splitClosedPending", () => {
  const NOW = new Date(2026, 4, 28, 10, 42, 0).getTime();

  it("空数组 → closed=[], pending=null", () => {
    expect(splitClosedPending([], "1h", NOW)).toEqual({
      closed: [],
      pending: null,
    });
  });

  it("最右端是 pending → 切出来", () => {
    const data = [
      { ts: new Date(2026, 4, 28, 8, 0, 0).getTime(), v: 1 },
      { ts: new Date(2026, 4, 28, 9, 0, 0).getTime(), v: 2 },
      { ts: new Date(2026, 4, 28, 10, 0, 0).getTime(), v: 3 },
    ];
    const result = splitClosedPending(data, "1h", NOW);
    expect(result.closed).toEqual([data[0], data[1]]);
    expect(result.pending).toEqual(data[2]);
  });

  it("最右端已结束 → 全是 closed", () => {
    const data = [
      { ts: new Date(2026, 4, 28, 7, 0, 0).getTime(), v: 1 },
      { ts: new Date(2026, 4, 28, 8, 0, 0).getTime(), v: 2 },
      { ts: new Date(2026, 4, 28, 9, 0, 0).getTime(), v: 3 },
    ];
    const result = splitClosedPending(data, "1h", NOW);
    expect(result.closed).toEqual(data);
    expect(result.pending).toBeNull();
  });

  it("只有一个点且 pending → closed=[], pending=该点", () => {
    const data = [
      { ts: new Date(2026, 4, 28, 10, 0, 0).getTime(), v: 1 },
    ];
    const result = splitClosedPending(data, "1h", NOW);
    expect(result.closed).toEqual([]);
    expect(result.pending).toEqual(data[0]);
  });
});

const HR = 60 * 60_000;

describe("densifyByBucket", () => {
  // 模拟一次 24h 断电:有数据的段在两端,中间整 24 个 1h bucket 缺失
  const NOW = new Date(2026, 5, 1, 9, 30, 0).getTime();
  const SINCE = NOW - 3 * 24 * HR;
  type P = { ts: number; v: number | null };
  const empty = (ts: number): P => ({ ts, v: null });

  it("3 天窗口 1h bucket: 中间 24 个空 bucket 全部被补出且字段为 null", () => {
    const tFirstBlock = new Date(2026, 4, 30, 0, 0, 0).getTime();
    const tLastBlock = new Date(2026, 4, 31, 8, 0, 0).getTime();
    const tAfter = new Date(2026, 5, 1, 9, 0, 0).getTime();
    const sparse: P[] = [
      { ts: tFirstBlock, v: 1 },
      { ts: tFirstBlock + HR, v: 2 },
      { ts: tLastBlock, v: 3 },
      { ts: tAfter, v: 4 },
    ];
    const dense = densifyByBucket(sparse, "1h", SINCE, NOW, empty);
    // 总长 = 包含 [SINCE 对齐起点, NOW 对齐起点] 的所有 1h bucket
    const start = Math.floor(SINCE / HR) * HR;
    const end = Math.floor(NOW / HR) * HR;
    expect(dense.length).toBe((end - start) / HR + 1);
    // 有真实数据的 4 个点保留原值
    expect(dense.find((p) => p.ts === tFirstBlock)?.v).toBe(1);
    expect(dense.find((p) => p.ts === tLastBlock)?.v).toBe(3);
    expect(dense.find((p) => p.ts === tAfter)?.v).toBe(4);
    // 断电时段中间任取一个 ts,应当被填成 null
    const midGap = tLastBlock + 12 * HR;
    const midPoint = dense.find((p) => p.ts === midGap);
    expect(midPoint).toBeDefined();
    expect(midPoint?.v).toBeNull();
  });

  it("空输入 + 有效区间 → 全部填空 bucket(语义:补齐时间轴,不是过滤)", () => {
    const start = NOW;
    const end = NOW + 2 * HR;
    const dense = densifyByBucket([] as P[], "1h", start, end, empty);
    expect(dense).toHaveLength(3);
    expect(dense.every((p) => p.v === null)).toBe(true);
  });

  it("since > until 时直接返回输入数据(非法区间不展开)", () => {
    const sparse: P[] = [{ ts: NOW, v: 1 }];
    const dense = densifyByBucket(sparse, "1h", NOW, NOW - HR, empty);
    expect(dense).toBe(sparse);
  });

  it("ts 不在 bucket 起点上时按 floor 对齐, 不会出现重复/丢失", () => {
    const aligned = Math.floor(NOW / HR) * HR;
    // 同 bucket 两个点, densify 后只剩一个 (后写覆盖前)
    const sparse: P[] = [
      { ts: aligned + 100, v: 1 },
      { ts: aligned + 500, v: 2 },
    ];
    const dense = densifyByBucket(sparse, "1h", aligned, aligned, empty);
    expect(dense).toHaveLength(1);
    expect(dense[0].v).toBe(2);
  });
});

describe("formatPerfTs", () => {
  const NOW = new Date(2026, 5, 1, 9, 30, 0).getTime();

  it("无 spanMs:1 小时前只显示 HH:MM", () => {
    const ts = NOW - HR;
    expect(formatPerfTs(ts, { now: NOW })).toBe("08:30");
  });

  it("无 spanMs:25 小时前加 M/D", () => {
    const ts = NOW - 25 * HR;
    expect(formatPerfTs(ts, { now: NOW })).toMatch(
      /^\d{1,2}\/\d{1,2} \d{2}:\d{2}$/,
    );
  });

  it("spanMs = 24h (24h 窗口):整图加日期(必跨一次午夜)", () => {
    const ts = NOW - HR;
    expect(formatPerfTs(ts, { now: NOW, spanMs: 24 * HR })).toBe("6/1 08:30");
  });

  it("spanMs = 6h:整图都只显示 HH:MM", () => {
    const ts = NOW - HR;
    expect(formatPerfTs(ts, { now: NOW, spanMs: 6 * HR })).toBe("08:30");
  });

  it("spanMs > 24h (3d 窗口):整图加日期", () => {
    const ts = NOW - HR;
    expect(formatPerfTs(ts, { now: NOW, spanMs: 3 * 24 * HR })).toBe(
      "6/1 08:30",
    );
  });
});
