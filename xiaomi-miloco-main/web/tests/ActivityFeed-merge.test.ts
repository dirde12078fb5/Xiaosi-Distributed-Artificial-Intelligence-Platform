/**
 * mergeAndSort — Activity feed 排序守门测试
 *
 * 背景:用户反馈"查看更早"翻页后,SSE 期间推的新事件夹杂在老事件中导致视觉乱序
 *      (17:14:02 → 17:37:56 → 17:37:49,降序断裂).
 *
 * 守住两个 invariant:
 *   - dedup by id(后到的字段覆盖先到)
 *   - timestamp DESC(最新在前)
 */
import { describe, it, expect } from "vitest";
import { mergeAndSort } from "@/components/ActivityFeed";
import type { ActivityEvent } from "@/lib/types";

function ev(id: string, ts: number, extras: Partial<ActivityEvent> = {}): ActivityEvent {
  return {
    id,
    timestamp: ts,
    text: "x",
    device_ids: [],
    snapshot_count: 0,
    ...extras,
  };
}

describe("mergeAndSort", () => {
  it("空+空 → 空", () => {
    expect(mergeAndSort([], [])).toEqual([]);
  });

  it("只一边有 → 排序保留", () => {
    const r = mergeAndSort([ev("a", 100), ev("b", 200), ev("c", 50)], []);
    expect(r.map((e) => e.id)).toEqual(["b", "a", "c"]); // DESC: 200, 100, 50
  });

  it("两边合并 → 严格 timestamp DESC", () => {
    // 重现用户截图场景:已有 17:37 段,append 拉来 17:14 段
    const primary = [
      ev("p1", new Date(2026, 5, 6, 17, 37, 56).getTime()),
      ev("p2", new Date(2026, 5, 6, 17, 37, 49).getTime()),
      ev("p3", new Date(2026, 5, 6, 17, 28, 18).getTime()),
    ];
    const secondary = [
      ev("s1", new Date(2026, 5, 6, 17, 14, 17).getTime()),
      ev("s2", new Date(2026, 5, 6, 17, 14, 2).getTime()),
    ];
    const r = mergeAndSort(primary, secondary);
    expect(r.map((e) => e.id)).toEqual(["p1", "p2", "p3", "s1", "s2"]);
  });

  it("dedup by id:secondary 覆盖 primary 同 id 的字段", () => {
    const primary = [ev("x", 100, { snapshot_count: 0, clip_kind: null })];
    const secondary = [ev("x", 100, { snapshot_count: 2, clip_kind: "mp4" })];
    const r = mergeAndSort(primary, secondary);
    expect(r).toHaveLength(1);
    expect(r[0].snapshot_count).toBe(2);
    expect(r[0].clip_kind).toBe("mp4");
  });

  it("dedup 后保持 timestamp DESC", () => {
    const primary = [ev("a", 100), ev("b", 50)];
    const secondary = [ev("c", 200), ev("a", 100, { snapshot_count: 9 })];
    const r = mergeAndSort(primary, secondary);
    expect(r.map((e) => e.id)).toEqual(["c", "a", "b"]); // 200, 100, 50
    expect(r[1].snapshot_count).toBe(9); // secondary 覆盖
  });

  it("回归用户截图:SSE 在 loadMore 期间推新事件不应让历史段乱序", () => {
    // 屏幕已有(SSE 累积 + 初始 fetch):17:37:xx ~ 17:28:xx
    const inMemory = [
      ev("e1", Date.parse("2026-06-06T17:37:56+08:00")),
      ev("e2", Date.parse("2026-06-06T17:37:49+08:00")),
      ev("e3", Date.parse("2026-06-06T17:28:18+08:00")),
    ];
    // loadMore 拉来更早一批 (17:14:xx ~ 17:15:xx)
    const fetched = [
      ev("e4", Date.parse("2026-06-06T17:15:05+08:00")),
      ev("e5", Date.parse("2026-06-06T17:14:57+08:00")),
      ev("e6", Date.parse("2026-06-06T17:14:02+08:00")),
    ];
    const r = mergeAndSort(inMemory, fetched);
    // 严格降序:e1 > e2 > e4 > e5 > e6 > e3?
    // 不对:e4 (17:15:05) 比 e2 (17:37:49) 早,所以 e2 应该排在 e4 前.
    // 而 e3 (17:28:18) 在 e4 之后.正确序列:e1, e2, e3, e4, e5, e6.
    expect(r.map((e) => e.id)).toEqual(["e1", "e2", "e3", "e4", "e5", "e6"]);
  });
});
