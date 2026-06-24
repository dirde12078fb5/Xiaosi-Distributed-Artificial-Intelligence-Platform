/**
 * 阶段统计表:7 阶段 × AVG / P50 / P75 / P95 / P99 / 样本数。
 *
 * P95 列按耗时降序排出 top3,分别用 1st/2nd/3rd 三档色高亮,定位"哪个阶段最慢"。
 * 颜色:1st=error 红 / 2nd=info 蓝 / 3rd=success 绿。
 */

import { useTranslation } from "react-i18next";
import type { TFunction } from "i18next";
import type { AsyncState } from "@/hooks/useAsync";
import type { PerfStageKey, PerfStagePercentiles } from "@/lib/types";

interface Props {
  state: AsyncState<PerfStagePercentiles>;
}

const STAGE_ORDER: PerfStageKey[] = [
  "decode_ms",
  "collect_ms",
  "convert_ms",
  "gate_ms",
  "identity_ms",
  "omni_ms",
  "log_ms",
];

const STAGE_LABEL: Record<PerfStageKey, string> = {
  decode_ms: "decode",
  collect_ms: "collect",
  convert_ms: "convert",
  gate_ms: "gate",
  identity_ms: "identity",
  omni_ms: "omni",
  log_ms: "log",
};

const RANK_TEXT_CLASS = ["text-error", "text-info", "text-success"];

export function PerfStageTable({ state }: Props) {
  const { t } = useTranslation();
  return (
    <section
      className="rounded-xl bg-bg-secondary border border-border shadow-sm p-5 md:p-6"
      aria-labelledby="perf-stage-title"
    >
      <div className="flex items-baseline justify-between flex-wrap gap-2 mb-4">
        <h2 id="perf-stage-title" className="text-title">
          {t("perf.stageTitle")}
        </h2>
        <span className="text-caption text-text-secondary">
          {t("perf.stageP95Top3")}
          <span className="text-error mx-1">● {t("perf.stageRank1st")}</span>
          <span className="text-info mx-1">● {t("perf.stageRank2nd")}</span>
          <span className="text-success mx-1">● {t("perf.stageRank3rd")}</span>
        </span>
      </div>

      {state.loading && !state.data ? (
        <div className="py-8 text-center text-text-secondary">{t("perf.loading")}</div>
      ) : state.error ? (
        <div className="py-8 text-center text-error">{state.error.message}</div>
      ) : state.data ? (
        <Table data={state.data} t={t} />
      ) : null}
    </section>
  );
}

function Table({ data, t }: { data: PerfStagePercentiles; t: TFunction }) {
  // 按 P95 降序排出 top3
  const sortedByP95 = [...STAGE_ORDER].sort(
    (a, b) => data[b].p95 - data[a].p95,
  );
  const rankOf = new Map<PerfStageKey, number>();
  sortedByP95.slice(0, 3).forEach((k, i) => rankOf.set(k, i));

  // 占比基准:所有非空阶段 avg 之和作为 100%(表内自洽口径)。
  const totalAvg = STAGE_ORDER.reduce(
    (sum, k) => sum + (data[k].sample_size > 0 ? data[k].avg : 0),
    0,
  );

  return (
    <div className="text-caption overflow-x-auto -mx-5 md:-mx-6">
      <table className="w-full">
        <thead>
          <tr className="text-text-secondary border-b border-border">
            <th className="text-left px-5 md:px-6 py-2">{t("perf.colStage")}</th>
            <th className="text-right px-3 py-2 num">{t("perf.colAvgMs")}</th>
            <th className="text-right px-3 py-2 num">{t("perf.colAvgPct")}</th>
            <th className="text-right px-3 py-2 num">{t("perf.colP50Ms")}</th>
            <th className="text-right px-3 py-2 num">{t("perf.colP75Ms")}</th>
            <th className="text-right px-3 py-2 num">{t("perf.colP95Ms")}</th>
            <th className="text-right px-3 py-2 num">{t("perf.colP99Ms")}</th>
            <th className="text-right px-5 md:px-6 py-2 num">{t("perf.colSampleSize")}</th>
          </tr>
        </thead>
        <tbody>
          {STAGE_ORDER.map((k) => {
            const row = data[k];
            const rank = rankOf.get(k);
            const rankCls =
              rank !== undefined ? RANK_TEXT_CLASS[rank] : "text-text-primary";
            const isEmpty = row.sample_size === 0;
            const pct = !isEmpty && totalAvg > 0 ? (row.avg / totalAvg) * 100 : 0;
            return (
              <tr
                key={k}
                className="border-b border-border last:border-b-0"
              >
                <td className="px-5 md:px-6 py-2.5 text-text-primary">
                  <span className="mono">{STAGE_LABEL[k]}</span>
                </td>
                <td
                  className={`px-3 py-2.5 text-right num ${
                    isEmpty ? "text-text-tertiary" : "text-text-secondary"
                  }`}
                >
                  {isEmpty ? "—" : row.avg.toFixed(1)}
                </td>
                <td
                  className={`px-3 py-2.5 text-right num ${
                    isEmpty ? "text-text-tertiary" : "text-text-secondary"
                  }`}
                >
                  {isEmpty ? "—" : `${pct.toFixed(2)}%`}
                </td>
                <td
                  className={`px-3 py-2.5 text-right num ${
                    isEmpty ? "text-text-tertiary" : "text-text-secondary"
                  }`}
                >
                  {isEmpty ? "—" : row.p50.toFixed(1)}
                </td>
                <td
                  className={`px-3 py-2.5 text-right num ${
                    isEmpty ? "text-text-tertiary" : "text-text-secondary"
                  }`}
                >
                  {isEmpty ? "—" : row.p75.toFixed(1)}
                </td>
                <td
                  className={`px-3 py-2.5 text-right num font-semibold ${
                    isEmpty ? "text-text-tertiary" : rankCls
                  }`}
                >
                  {isEmpty ? "—" : row.p95.toFixed(1)}
                </td>
                <td
                  className={`px-3 py-2.5 text-right num ${
                    isEmpty ? "text-text-tertiary" : "text-text-secondary"
                  }`}
                >
                  {isEmpty ? "—" : row.p99.toFixed(1)}
                </td>
                <td className="px-5 md:px-6 py-2.5 text-right num text-text-tertiary">
                  {row.sample_size.toLocaleString()}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
