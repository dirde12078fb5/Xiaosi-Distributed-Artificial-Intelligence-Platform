/**
 * Perf 图表共享的 bucket 工具。
 *
 * 后端 stats SQL 按 (ts/bms)*bms 对齐到 bucket 起点。当一个 bucket 还在累积
 * 中(start + bms > now),桶内样本不足,AVG/P95 会跳到 0 或异常值。
 * Perf 图表统一把这种"未结束"的最右端点标为 pending,渲染时降级显示。
 */

import i18n from "@/i18n";
import type { PerfBucket, PerfWindow } from "./types";

export const BUCKET_MS: Record<PerfBucket, number> = {
  "1m": 60_000,
  "5m": 5 * 60_000,
  "1h": 60 * 60_000,
  "1d": 24 * 60 * 60_000,
};

export const WINDOW_MS: Record<PerfWindow, number> = {
  "1h": 60 * 60_000,
  "6h": 6 * 60 * 60_000,
  "24h": 24 * 60 * 60_000,
  "3d": 3 * 24 * 60 * 60_000,
};

/** Perf 视图统一的时间窗口选项(PerfPage / PerfInline 共用)。 */
export function perfWindows(): { key: PerfWindow; label: string }[] {
  return [
    { key: "1h", label: i18n.t("perf.windowLast1h") },
    { key: "6h", label: i18n.t("perf.windowLast6h") },
    { key: "24h", label: i18n.t("perf.windowLast24h") },
    { key: "3d", label: i18n.t("perf.windowLast3d") },
  ];
}

/** 窗口 → 默认 bucket 粒度:1h→1m,6h→5m,24h/3d→1h。 */
export function defaultBucket(w: PerfWindow): PerfBucket {
  if (w === "24h" || w === "3d") return "1h";
  if (w === "1h") return "1m";
  return "5m";
}

/** 最右端 bucket 是否还在累积中(起点 + 一个 bucket 长度 > now)。 */
export function isPendingBucket(
  ts: number,
  bucket: PerfBucket,
  now: number = Date.now(),
): boolean {
  return ts + BUCKET_MS[bucket] > now;
}

/** 把 series 拆成已结束段(closed)和最右端未结束点(pending)。
 *  pending 为 null 表示最右端点已是完整 bucket。 */
export function splitClosedPending<T extends { ts: number }>(
  data: T[],
  bucket: PerfBucket,
  now: number = Date.now(),
): { closed: T[]; pending: T | null } {
  if (data.length === 0) return { closed: [], pending: null };
  const last = data[data.length - 1];
  if (isPendingBucket(last.ts, bucket, now)) {
    return { closed: data.slice(0, -1), pending: last };
  }
  return { closed: data, pending: null };
}

/**
 * 按 bucket 步长把稀疏数据补齐成等距时间序列,缺失 bucket 用 emptyOf(ts) 填。
 *
 * 背景: backend stats SQL 大多是 `GROUP BY ts ORDER BY ts`,空 bucket 直接不
 * 返回行。前端图表按数组下标等距画 X 轴,服务停机/断电这种长空洞会被压缩到
 * 跟正常 bucket 一样宽,实线连过去看起来像连续运行。densify 后图表按真实
 * 时间间距渲染,折线 chart 在 emptyOf 字段为 null 时自动断开,柱状 chart 空
 * bucket 高度为 0 → 视觉上是空白带,gap 一眼可见。
 *
 * since/until 用客户端 Date.now() 推, 跟 backend _window() 的 server now 差几
 * 秒, 但 bucket 起点对齐到 (ts/bms)*bms 后误差不超过一个 bucket,可忽略。
 */
export function densifyByBucket<T extends { ts: number }>(
  data: T[],
  bucket: PerfBucket,
  since: number,
  until: number,
  emptyOf: (ts: number) => T,
): T[] {
  const bms = BUCKET_MS[bucket];
  const start = Math.floor(since / bms) * bms;
  const end = Math.floor(until / bms) * bms;
  if (start > end) return data;
  const byTs = new Map<number, T>();
  for (const d of data) byTs.set(Math.floor(d.ts / bms) * bms, d);
  const out: T[] = [];
  for (let ts = start; ts <= end; ts += bms) {
    out.push(byTs.get(ts) ?? emptyOf(ts));
  }
  return out;
}

/** 判断 densify 填出来的空 bucket:除 ts 外所有字段均为 null。 */
export function isEmptyBucket<T extends { ts: number }>(p: T): boolean {
  for (const k in p) {
    if (k === "ts") continue;
    if ((p as Record<string, unknown>)[k] != null) return false;
  }
  return true;
}

/** 扫描连续无数据的 bucket,合并成 [startIdx, endIdx] 区间数组。
 *  pendingIdx(最右端正在累积的桶)被排除 — 技术上未结束,不算空白历史。 */
export function findGapRegions<T extends { ts: number }>(
  data: T[],
  pendingIdx: number,
): { startIdx: number; endIdx: number }[] {
  const regions: { startIdx: number; endIdx: number }[] = [];
  let gapStart: number | null = null;
  for (let i = 0; i < data.length; i++) {
    const empty = i !== pendingIdx && isEmptyBucket(data[i]);
    if (empty) {
      if (gapStart === null) gapStart = i;
    } else if (gapStart !== null) {
      regions.push({ startIdx: gapStart, endIdx: i - 1 });
      gapStart = null;
    }
  }
  if (gapStart !== null) {
    regions.push({ startIdx: gapStart, endIdx: data.length - 1 });
  }
  return regions;
}

/**
 * 性能图表统一的时间格式化。
 *
 * 何时加 M/D 前缀:
 *   1. spanMs 指定且 >= 24h —— 整张图都加,避免跨午夜时同图前后突变
 *      (24h 窗口最左点必跨一次午夜,3d 跨更多)
 *   2. 没传 spanMs 时退化为"距 now >= 24h 加日期"的快捷判定
 *
 * spanMs 传调用方所在图的窗口跨度(WINDOW_MS[windowKey])。
 */
const NEED_DATE_THRESHOLD_MS = 24 * 60 * 60_000;
export function formatPerfTs(
  ms: number,
  opts: { spanMs?: number; now?: number; withSec?: boolean } = {},
): string {
  const now = opts.now ?? Date.now();
  const d = new Date(ms);
  const hh = String(d.getHours()).padStart(2, "0");
  const mm = String(d.getMinutes()).padStart(2, "0");
  const ss = String(d.getSeconds()).padStart(2, "0");
  const time = opts.withSec ? `${hh}:${mm}:${ss}` : `${hh}:${mm}`;
  const needDate =
    opts.spanMs != null
      ? opts.spanMs >= NEED_DATE_THRESHOLD_MS
      : now - ms >= NEED_DATE_THRESHOLD_MS;
  if (!needDate) return time;
  return `${d.getMonth() + 1}/${d.getDate()} ${time}`;
}
