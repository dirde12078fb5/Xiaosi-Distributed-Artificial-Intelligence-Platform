/**
 * 时间分布图：纯 SVG 柱状图（受控）。周期由 UsagePage 统一控制并传入；
 * today 额外支持切换 bin 大小（10分/1时/3小时）——raw 事件带毫秒时间戳，可任意分桶；
 * week/month 走 daily rollup 只有「天」粒度，故不显示 bin 选项。
 *
 * 不引第三方图表库；柱高 = tokens 占全段最大值的百分比；悬停显示具体 tokens + 时间。
 */

import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import type { UsagePeriod, UsageStats } from "@/lib/types";
import { humanTokensShort } from "@/lib/formatTokens";
import { Segmented } from "./Segmented";

const BIN_OPTIONS: { minutes: number; labelKey: string }[] = [
  { minutes: 10, labelKey: "usage.bin10min" },
  { minutes: 60, labelKey: "usage.bin1hour" },
  { minutes: 180, labelKey: "usage.bin3hour" },
];

function formatTimelineLabel(
  ts: string,
  period: UsagePeriod,
  binMinutes: number,
): string {
  const d = new Date(ts);
  if (period === "today") {
    const hh = d.getHours().toString().padStart(2, "0");
    if (binMinutes < 60) {
      return `${hh}:${d.getMinutes().toString().padStart(2, "0")}`;
    }
    return `${hh}h`;
  }
  // week / month: 显示 "M/D"
  return `${d.getMonth() + 1}/${d.getDate()}`;
}

/** 横轴标签密度：today 桶数随 bin 变化，自适应到约 12 个标签；month 每 5 天。 */
function shouldShowLabel(i: number, total: number, period: UsagePeriod): boolean {
  if (period === "week") return true;
  if (period === "month") return i % 5 === 0 || i === total - 1;
  // today：只标桶「起始」边界，按 step 抽稀；末尾的 24h 由单独的结束刻度负责。
  const step = Math.max(1, Math.ceil(total / 12));
  return i % step === 0;
}

/** 把动态最大值向上取整成漂亮数（1/2/5 × 10ⁿ），作纵轴上限——标签干净且顶部留头部空隙。 */
function niceCeil(v: number): number {
  if (v <= 0) return 1;
  const base = Math.pow(10, Math.floor(Math.log10(v)));
  const f = v / base; // 1..10
  const nice = f <= 1 ? 1 : f <= 2 ? 2 : f <= 5 ? 5 : 10;
  return nice * base;
}

export function UsageTimelineChart({
  stats,
  binMinutes,
  onBinChange,
  embedded = false,
}: {
  stats: UsageStats;
  binMinutes: number;
  onBinChange: (minutes: number) => void;
  embedded?: boolean;
}) {
  const { t } = useTranslation();
  // 用 stats.period（数据自带的周期）而非外部选中值，避免切换时数据未到位却用新周期
  // 格式化横轴导致的瞬态错渲染。
  const period = stats.period;
  // hover 状态：高亮某一根柱
  const [hoverIdx, setHoverIdx] = useState<number | null>(null);
  useEffect(() => setHoverIdx(null), [period, binMinutes]);

  return (
    <section
      className={
        embedded
          ? ""
          : "rounded-xl bg-bg-secondary border border-border shadow-sm p-5 md:p-6"
      }
      aria-labelledby="usage-timeline-title"
    >
      <div className="flex items-baseline justify-between flex-wrap gap-3 mb-4">
        <h2 id="usage-timeline-title" className="text-title">{t("usage.timelineTitle")}</h2>
        {period === "today" && (
          <Segmented
            ariaLabel={t("usage.granularityAria")}
            value={binMinutes}
            onChange={onBinChange}
            options={BIN_OPTIONS.map((b) => ({ key: b.minutes, label: t(b.labelKey) }))}
          />
        )}
      </div>

      <Chart
        data={stats.timeline}
        period={period}
        binMinutes={binMinutes}
        hoverIdx={hoverIdx}
        setHoverIdx={setHoverIdx}
      />
    </section>
  );
}

interface ChartProps {
  data: { ts: string; tokens: number }[];
  period: UsagePeriod;
  binMinutes: number;
  hoverIdx: number | null;
  setHoverIdx: (i: number | null) => void;
}

/** 纯 SVG 柱状图。viewBox 固定，按容器宽度自适应。 */
function Chart({ data, period, binMinutes, hoverIdx, setHoverIdx }: ChartProps) {
  const { t } = useTranslation();
  const W = 800;
  const H = 200;
  const padL = 44; // 左留白给纵轴数值标签，柱子从这里起，标签不再压到首根柱
  const padR = 0;
  const padT = 20;
  const padB = 28;
  const innerW = W - padL - padR;
  const innerH = H - padT - padB;

  // 用 reduce 不用 Math.max(...spread) — period=year 等场景 data.length 可能 365+,
  // spread 大数组栈溢出风险;reduce 线性安全。
  const max = data.reduce((m, d) => Math.max(m, d.tokens), 1);
  const niceMax = niceCeil(max); // 纵轴上限（动态取整），柱高与网格线都以它为基准
  const n = data.length;
  // 桶数多时收窄间距，避免 barW 变负（today 10 分钟桶达 144 个）。
  const barGap = n > 150 ? 0 : n > 50 ? 1 : period === "today" ? 2 : 4;
  const barW = n > 0 ? Math.max((innerW - barGap * (n - 1)) / n, 0.5) : 0;

  const CHART_H = 220; // SVG 渲染像素高（固定）；viewBox→px 换算用它

  return (
    <div className="relative w-full" style={{ height: CHART_H }}>
      {/* 柱 + 网格线放 SVG（非等比拉伸对矩形/线无影响）；坐标轴文字一律走 HTML，避免被横向拉伸 */}
      <svg
        viewBox={`0 0 ${W} ${H}`}
        className="w-full block"
        style={{ height: CHART_H }}
        preserveAspectRatio="none"
        role="img"
        aria-label={t("usage.chartAriaLabel")}
      >
        {/* 纵轴网格线 */}
        {[0, 0.5, 1].map((ratio) => {
          const gy = H - padB - ratio * innerH;
          return (
            <line
              key={ratio}
              x1={padL}
              y1={gy}
              x2={W - padR}
              y2={gy}
              className={ratio === 0 ? "stroke-border" : "stroke-border opacity-40"}
              strokeWidth="1"
              strokeDasharray={ratio === 0 ? undefined : "3 3"}
            />
          );
        })}

        {/* 柱 */}
        {data.map((d, i) => {
          const h = (d.tokens / niceMax) * innerH;
          const x = padL + i * (barW + barGap);
          const y = H - padB - h;
          const on = hoverIdx === i;
          return (
            <g
              key={d.ts}
              onMouseEnter={() => setHoverIdx(i)}
              onMouseLeave={() => setHoverIdx(null)}
              style={{ cursor: "pointer" }}
            >
              {/* 透明 hit-box，让贴近的鼠标也能命中（柱子很瘦时）*/}
              <rect
                x={x}
                y={padT}
                width={barW + barGap}
                height={H - padT - padB}
                fill="transparent"
              />
              <rect
                x={x}
                y={y}
                width={barW}
                height={h}
                rx={Math.min(barW / 4, 3)}
                className={on ? "fill-brand-primary" : "fill-info opacity-70"}
              />
            </g>
          );
        })}
      </svg>

      {/* 纵轴数值标签（HTML，右对齐在左留白区、垂直居中到网格线）*/}
      {[0, 0.5, 1].map((ratio) => {
        const gy = H - padB - ratio * innerH;
        return (
          <div
            key={ratio}
            className="text-caption num text-text-tertiary text-right pr-1.5 pointer-events-none"
            style={{
              position: "absolute",
              left: 0,
              width: `${(padL / W) * 100}%`,
              top: `${(gy / H) * CHART_H}px`,
              transform: "translateY(-50%)",
            }}
          >
            {humanTokensShort(niceMax * ratio)}
          </div>
        );
      })}

      {/* x 轴刻度标签（HTML，落在桶左边界；首桶左对齐）*/}
      {data.map((d, i) => {
        if (!shouldShowLabel(i, n, period)) return null;
        const atStart = i === 0;
        const x = atStart ? padL : padL + i * (barW + barGap) - barGap / 2;
        return (
          <div
            key={d.ts}
            className="text-caption num text-text-tertiary pointer-events-none whitespace-nowrap"
            style={{
              position: "absolute",
              left: `${(x / W) * 100}%`,
              bottom: 2,
              transform: atStart ? "none" : "translateX(-50%)",
            }}
          >
            {formatTimelineLabel(d.ts, period, binMinutes)}
          </div>
        );
      })}

      {/* today：右端 24h 结束刻度 */}
      {period === "today" && (
        <div
          className="text-caption num text-text-tertiary pointer-events-none whitespace-nowrap"
          style={{ position: "absolute", right: 0, bottom: 2 }}
        >
          {binMinutes < 60 ? "24:00" : "24h"}
        </div>
      )}

      {/* hover tooltip（HTML 浮层）：定位到所悬停柱子正上方 */}
      {hoverIdx != null &&
        data[hoverIdx] &&
        (() => {
          const cx = padL + hoverIdx * (barW + barGap) + barW / 2;
          const leftPct = (cx / W) * 100;
          // 柱顶（viewBox→px：SVG 渲染高 220、viewBox 高 H）；高柱时下钳到 48px 留出上方空间
          const barTopPx =
            ((H - padB - (data[hoverIdx].tokens / niceMax) * innerH) / H) * CHART_H;
          const anchorY = Math.max(barTopPx, 48);
          return (
            <div
              className="text-caption absolute z-10 px-2.5 py-1.5 rounded-lg bg-bg-secondary border border-border shadow-sm pointer-events-none whitespace-nowrap text-center"
              style={{
                left: `${leftPct}%`,
                top: `${anchorY}px`,
                transform: "translate(-50%, calc(-100% - 6px))",
              }}
            >
              <div className="num text-text-primary">
                {t("usage.tokensTooltip", { value: humanTokensShort(data[hoverIdx].tokens) })}
              </div>
              <div className="text-text-secondary num">
                {formatTimelineLabel(data[hoverIdx].ts, period, binMinutes)}
              </div>
            </div>
          );
        })()}
    </div>
  );
}
