/**
 * 总览：大字 token 总数 + 调用次数 / 缓存命中 + 模态构成饼图。
 * 展示周期由 UsagePage 统一控制并通过 stats.period 传入（标题随之变化）。
 */

import { useState } from "react";
import { useTranslation } from "react-i18next";
import type { TokenBreakdown, UsagePeriod, UsageStats } from "@/lib/types";
import { clearUsageData } from "@/api";
import { humanTokens } from "@/lib/formatTokens";
import { Segmented } from "./Segmented";
import { toast } from "./Toast";

const PERIOD_KEYS: Record<UsagePeriod, string> = {
  today: "usage.periodToday",
  week: "usage.periodWeek",
  month: "usage.periodMonth",
};

// 柔和偏暗的低饱和配色：避免高亮刺眼；浅底上用"压暗的色值"而非降透明度（降透明只会更淡）。
// 音频用偏暗的金黄，跟视频的哑橙拉开区分。
const COLOR = {
  // 蓝与时间分布柱子对齐：info(#2563EB) @ opacity-70 叠在白卡上的等效实色。
  text: "#6692F1",
  video: "#F2A468", // 暖橙
  audio: "#F0C94C", // 金黄
  output: "#63C589", // 绿
};

interface Seg {
  label: string;
  value: number;
  color: string;
}

/** 模态构成：文本 = input − video − audio；只列非零项。 */
function modalitySegments(b: TokenBreakdown, t: (k: string) => string): Seg[] {
  const text = Math.max(b.input - b.video - b.audio, 0);
  return [
    { label: t("usage.modalityText"), value: text, color: COLOR.text },
    { label: t("usage.modalityVideo"), value: b.video, color: COLOR.video },
    { label: t("usage.modalityAudio"), value: b.audio, color: COLOR.audio },
    { label: t("usage.modalityOutput"), value: b.output, color: COLOR.output },
  ].filter((s) => s.value > 0);
}

/** SVG 弧形饼图（扇区分界与圆边都走浏览器抗锯齿，避免 conic-gradient 的锯齿）。 */
function Pie({ segments, size = 190 }: { segments: Seg[]; size?: number }) {
  const nonzero = segments.filter((s) => s.value > 0);
  const total = nonzero.reduce((s, x) => s + x.value, 0);
  const R = 50;
  const C = 50; // viewBox 100×100，圆心 (50,50) 半径 50

  if (total <= 0) {
    return (
      <div
        className="rounded-full bg-bg-primary shrink-0"
        style={{ width: size, height: size }}
        aria-hidden
      />
    );
  }

  // 只有一个非零扇区时画整圆，避免起止角相同的退化弧
  if (nonzero.length === 1) {
    return (
      <svg width={size} height={size} viewBox="0 0 100 100" className="shrink-0" aria-hidden>
        <circle cx={C} cy={C} r={R} fill={nonzero[0].color} />
      </svg>
    );
  }

  let acc = 0;
  const paths = nonzero.map((s) => {
    const a0 = (acc / total) * 2 * Math.PI;
    acc += s.value;
    const a1 = (acc / total) * 2 * Math.PI;
    const x0 = C + R * Math.sin(a0);
    const y0 = C - R * Math.cos(a0);
    const x1 = C + R * Math.sin(a1);
    const y1 = C - R * Math.cos(a1);
    const large = a1 - a0 > Math.PI ? 1 : 0;
    return (
      <path
        key={s.label}
        d={`M ${C} ${C} L ${x0.toFixed(3)} ${y0.toFixed(3)} A ${R} ${R} 0 ${large} 1 ${x1.toFixed(3)} ${y1.toFixed(3)} Z`}
        fill={s.color}
      />
    );
  });

  return (
    <svg width={size} height={size} viewBox="0 0 100 100" className="shrink-0" aria-hidden>
      {paths}
    </svg>
  );
}

/** 饼图 + 标题 + 图例（名称 / token / 占比），整体居中竖排。 */
function PieBlock({ title, segments }: { title?: string; segments: Seg[] }) {
  const { t } = useTranslation();
  const total = segments.reduce((s, x) => s + x.value, 0);
  return (
    <div className="flex-1 min-w-[280px] flex justify-center">
      <div className="flex items-center gap-5">
        <div className="flex flex-col items-center">
          {title ? (
            <div className="text-body font-medium text-text-primary text-center mb-3">
              {title}
            </div>
          ) : null}
          <Pie segments={segments} />
        </div>
        <div className="text-caption flex flex-col gap-1.5">
          {segments.length === 0 ? (
            <span className="text-text-tertiary">{t("usage.noUsage")}</span>
          ) : (
            segments.map((s) => {
              const pct = total > 0 ? (s.value / total) * 100 : 0;
              return (
                <span key={s.label} className="inline-flex items-center gap-1.5">
                  <span
                    className="inline-block w-2 h-2 rounded-full shrink-0"
                    style={{ background: s.color }}
                  />
                  <span className="text-text-primary">{s.label}</span>
                  <span className="num text-text-tertiary">
                    {humanTokens(s.value)}
                  </span>
                  <span className="num text-text-tertiary">{pct.toFixed(1)}%</span>
                </span>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}

interface Props {
  stats: UsageStats;
  period: UsagePeriod;
  onPeriodChange: (p: UsagePeriod) => void;
  /** 清空用量数据成功后回调（让上层重取）。 */
  onCleared?: () => void;
  /** 嵌入「Token 用量」大格时去掉自身卡片外壳。 */
  embedded?: boolean;
}

export function UsageTodayOverview({
  stats,
  period,
  onPeriodChange,
  onCleared,
  embedded = false,
}: Props) {
  const { t } = useTranslation();
  const { totals } = stats;
  const [confirming, setConfirming] = useState(false);
  const [clearing, setClearing] = useState(false);

  const periodOptions = (Object.keys(PERIOD_KEYS) as UsagePeriod[]).map((k) => ({
    key: k,
    label: t(PERIOD_KEYS[k]),
  }));

  async function doClear() {
    setClearing(true);
    try {
      await clearUsageData();
      setConfirming(false);
      toast(t("usage.clearSuccess"), "ok");
      onCleared?.();
    } catch (e) {
      toast(e instanceof Error ? e.message : t("usage.clearFailed"), "danger");
    } finally {
      setClearing(false);
    }
  }

  return (
    <section
      className={
        embedded
          ? ""
          : "rounded-xl bg-bg-secondary border border-border shadow-sm p-5 md:p-6"
      }
      aria-labelledby="usage-today-title"
    >
      {/* 标题 + 清空 + 周期选择器（右上角，与时间分布卡的粒度选择器统一） */}
      <div className="flex items-baseline justify-between flex-wrap gap-3 mb-4">
        <h2 id="usage-today-title" className="text-title">
          {t("usage.overviewHeading", { period: t(PERIOD_KEYS[stats.period]) })}
        </h2>
        <div className="flex items-center gap-3">
          {confirming ? (
            <span className="inline-flex items-center gap-2 text-caption">
              <span className="text-text-secondary">{t("usage.clearConfirmPrompt")}</span>
              <button
                type="button"
                onClick={doClear}
                disabled={clearing}
                className="px-2.5 py-1 rounded-md bg-error text-white hover:opacity-90 disabled:opacity-60"
              >
                {clearing ? t("usage.clearing") : t("usage.clearConfirm")}
              </button>
              <button
                type="button"
                onClick={() => setConfirming(false)}
                disabled={clearing}
                className="px-2.5 py-1 rounded-md bg-bg-primary border border-border text-text-primary"
              >
                {t("usage.cancel")}
              </button>
            </span>
          ) : (
            <button
              type="button"
              onClick={() => setConfirming(true)}
              className="text-caption text-text-tertiary hover:text-error"
            >
              {t("usage.clearData")}
            </button>
          )}
          <Segmented
            ariaLabel={t("usage.statsPeriodAria")}
            value={period}
            onChange={onPeriodChange}
            options={periodOptions}
          />
        </div>
      </div>

      {/* 大数字(调用次数 / 缓存命中已移到明细表按模型展示) */}
      <div className="flex items-baseline gap-3 mb-5">
        <span className="text-display-lg num text-text-primary">
          {humanTokens(stats.total_tokens)}
        </span>
        <span className="text-title text-text-secondary font-normal">{t("usage.tokensUnit")}</span>
      </div>

      {/* 模态构成饼图(单饼,标题省略——图例已标明各模态) */}
      <div className="flex flex-wrap gap-x-8 gap-y-5">
        <PieBlock segments={modalitySegments(totals, t)} />
      </div>
    </section>
  );
}
