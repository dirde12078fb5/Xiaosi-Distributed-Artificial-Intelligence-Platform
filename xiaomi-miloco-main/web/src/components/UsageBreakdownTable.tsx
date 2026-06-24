/**
 * 明细表:按**模型**一行(合并实时/用户两类调用),列出 调用次数 / 各模态 token。
 * 数据来自 backend omni 计费(cache/video/audio 均为 input 的子集)。
 */

import { useTranslation } from "react-i18next";
import type { TokenBreakdown, UsageStats } from "@/lib/types";
import { humanTokens } from "@/lib/formatTokens";

interface ModelRow {
  model: string;
  calls: number;
  breakdown: TokenBreakdown;
}

/** 把 model×type 明细行按模型合并(累加调用数与各模态),模型名升序。 */
function rowsByModel(stats: UsageStats): ModelRow[] {
  const byModel = new Map<string, ModelRow>();
  for (const r of stats.rows) {
    let m = byModel.get(r.model);
    if (!m) {
      m = {
        model: r.model,
        calls: 0,
        breakdown: { input: 0, output: 0, cache: 0, video: 0, audio: 0 },
      };
      byModel.set(r.model, m);
    }
    m.calls += r.calls;
    m.breakdown.input += r.breakdown.input;
    m.breakdown.output += r.breakdown.output;
    m.breakdown.cache += r.breakdown.cache;
    m.breakdown.video += r.breakdown.video;
    m.breakdown.audio += r.breakdown.audio;
  }
  return [...byModel.values()].sort((a, b) =>
    a.model < b.model ? -1 : a.model > b.model ? 1 : 0,
  );
}

interface Props {
  stats: UsageStats;
  /** 嵌入「Token 用量」大格时去掉自身卡片外壳。 */
  embedded?: boolean;
}

export function UsageBreakdownTable({ stats, embedded = false }: Props) {
  const { t } = useTranslation();
  const rows = rowsByModel(stats);
  return (
    <section
      className={
        embedded
          ? ""
          : "rounded-xl bg-bg-secondary border border-border shadow-sm p-5 md:p-6"
      }
      aria-labelledby="usage-breakdown-title"
    >
      <h2 id="usage-breakdown-title" className="text-title mb-4">
        {t("usage.breakdownTitle")}
      </h2>

      <div className="text-caption overflow-x-auto -mx-5 md:-mx-6">
        <table className="w-full whitespace-nowrap">
          <thead>
            <tr className="text-text-secondary border-b border-border">
              <th className="text-left px-5 md:px-6 py-2">{t("usage.colModel")}</th>
              <th className="text-right px-3 py-2 num">{t("usage.colCalls")}</th>
              <th className="text-right px-3 py-2 num">{t("usage.colInput")}</th>
              <th className="text-right px-3 py-2 num">{t("usage.colOutput")}</th>
              <th className="text-right px-3 py-2 num">{t("usage.colCache")}</th>
              <th className="text-right px-3 py-2 num">{t("usage.colCacheHitRate")}</th>
              <th className="text-right px-3 py-2 num">{t("usage.colVideo")}</th>
              <th className="text-right px-5 md:px-6 py-2 num">{t("usage.colAudio")}</th>
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 ? (
              <tr>
                <td
                  colSpan={8}
                  className="px-5 md:px-6 py-6 text-center text-text-tertiary"
                >
                  {t("usage.noUsageData")}
                </td>
              </tr>
            ) : (
              rows.map((r) => (
                <tr
                  key={r.model}
                  className="border-b border-border last:border-b-0"
                >
                  <td className="px-5 md:px-6 py-2.5 text-text-primary">
                    {r.model}
                  </td>
                  <td className="px-3 py-2.5 text-right num text-text-secondary">
                    {r.calls.toLocaleString()}
                  </td>
                  <td className="px-3 py-2.5 text-right num text-text-primary">
                    {humanTokens(r.breakdown.input)}
                  </td>
                  <td className="px-3 py-2.5 text-right num text-text-primary">
                    {humanTokens(r.breakdown.output)}
                  </td>
                  <td className="px-3 py-2.5 text-right num text-text-tertiary">
                    {humanTokens(r.breakdown.cache)}
                  </td>
                  <td className="px-3 py-2.5 text-right num text-text-secondary">
                    {r.breakdown.input > 0
                      ? `${((r.breakdown.cache / r.breakdown.input) * 100).toFixed(1)}%`
                      : "—"}
                  </td>
                  <td className="px-3 py-2.5 text-right num text-text-tertiary">
                    {humanTokens(r.breakdown.video)}
                  </td>
                  <td className="px-5 md:px-6 py-2.5 text-right num text-text-tertiary">
                    {humanTokens(r.breakdown.audio)}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <p className="text-caption text-text-tertiary mt-3">
        {t("usage.breakdownNote")}
      </p>
    </section>
  );
}
