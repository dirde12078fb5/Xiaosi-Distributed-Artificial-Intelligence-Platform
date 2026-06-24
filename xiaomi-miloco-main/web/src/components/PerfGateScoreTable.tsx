/**
 * Gate 打分分布表:per-device × (video / audio) × P50 / P75 / P90 / P99 / 样本。
 *
 * 配合上方 PerfGateChart 看:过滤率告诉"多少 cycle 被拦下",这张表告诉"实际打分
 * 集中在什么水位"。表脚带配置阈值参考,便于判断阈值是否设得合理。
 *
 * 配置阈值默认值同步自 backend GateConfig (change_threshold / audio_energy_threshold);
 * 当前 hardcode,待后端暴露 /api/settings 的 gate 段后可改成动态读。
 */

import { useTranslation } from "react-i18next";
import type { TFunction } from "i18next";
import type { AsyncState } from "@/hooks/useAsync";
import type {
  PerceptionCamera,
  PerfGateScorePcts,
  PerfGateScoreRow,
} from "@/lib/types";

interface Props {
  state: AsyncState<PerfGateScoreRow[]>;
  /** id → friendly name 映射来源。空数组时单元格降级显示 device_id。 */
  cameras: PerceptionCamera[];
}

const VIDEO_THRESHOLD = 0.005; // GateConfig.change_threshold
const AUDIO_THRESHOLD = 0.01; // GateConfig.audio_energy_threshold

export function PerfGateScoreTable({ state, cameras }: Props) {
  const { t } = useTranslation();
  const idToName = new Map(cameras.map((c) => [c.did, c.name]));
  return (
    <section
      className="rounded-xl bg-bg-secondary border border-border shadow-sm p-5 md:p-6"
      aria-labelledby="perf-gate-score-title"
    >
      <div className="flex items-baseline justify-between flex-wrap gap-2 mb-4">
        <h2 id="perf-gate-score-title" className="text-title">
          {t("perf.gateScoreTitle")}
        </h2>
        <span className="text-caption text-text-tertiary">
          {t("perf.gateScoreThreshold", {
            video: VIDEO_THRESHOLD,
            audio: AUDIO_THRESHOLD,
          })}
        </span>
      </div>

      {state.loading && !state.data ? (
        <div className="py-8 text-center text-text-secondary">{t("perf.loading")}</div>
      ) : state.error ? (
        <div className="py-8 text-center text-error">{state.error.message}</div>
      ) : state.data && state.data.length > 0 ? (
        <Table rows={state.data} idToName={idToName} t={t} />
      ) : (
        <div className="py-8 text-center text-text-secondary">
          {t("perf.gateScoreEmpty")}
        </div>
      )}
    </section>
  );
}

function fmt(v: number | null): string {
  if (v == null) return "—";
  // 定点 6 位小数覆盖 visual_change_score / audio_energy_level 实际取值范围
  // (1e-5 ~ 1.0),避免科学计数法在小数值时反直觉。
  return v.toFixed(6);
}

/** 单个 percentile 单元格:percentile 值 >= 阈值时高亮(代表实际触发过 gate)。 */
function PctCell({
  pcts,
  pct,
  threshold,
}: {
  pcts: PerfGateScorePcts;
  pct: "p50" | "p75" | "p90" | "p99";
  threshold: number;
}) {
  const v = pcts[pct];
  const empty = v == null;
  const overThreshold = !empty && v >= threshold;
  return (
    <td
      className={`px-3 py-2.5 text-right num ${
        empty
          ? "text-text-tertiary"
          : overThreshold
            ? "text-success font-semibold"
            : "text-text-secondary"
      }`}
    >
      {fmt(v)}
    </td>
  );
}

function Table({
  rows,
  idToName,
  t,
}: {
  rows: PerfGateScoreRow[];
  idToName: Map<string, string>;
  t: TFunction;
}) {
  return (
    <div className="text-caption overflow-x-auto -mx-5 md:-mx-6">
      <table className="w-full">
        <thead>
          <tr className="text-text-secondary border-b border-border">
            <th className="text-left px-5 md:px-6 py-2">{t("perf.colDevice")}</th>
            <th className="text-left px-3 py-2">{t("perf.colRoom")}</th>
            <th className="text-right px-3 py-2 num">{t("perf.colVideoP50")}</th>
            <th className="text-right px-3 py-2 num">{t("perf.colP75")}</th>
            <th className="text-right px-3 py-2 num">{t("perf.colP90")}</th>
            <th className="text-right px-3 py-2 num">{t("perf.colP99")}</th>
            <th className="text-right px-3 py-2 num text-text-tertiary">{t("perf.colN")}</th>
            <th className="text-right px-3 py-2 num">{t("perf.colAudioP50")}</th>
            <th className="text-right px-3 py-2 num">{t("perf.colP75")}</th>
            <th className="text-right px-3 py-2 num">{t("perf.colP90")}</th>
            <th className="text-right px-3 py-2 num">{t("perf.colP99")}</th>
            <th className="text-right px-5 md:px-6 py-2 num text-text-tertiary">
              {t("perf.colN")}
            </th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => {
            // A 方案:friendly name 主、id 副小字。映射缺失时只显示 id。
            const friendlyName = idToName.get(row.device_id);
            return (
            <tr
              key={row.device_id}
              className="border-b border-border last:border-b-0"
            >
              <td className="px-5 md:px-6 py-2.5">
                {friendlyName ? (
                  <>
                    <div className="text-text-primary">{friendlyName}</div>
                    <div className="text-text-tertiary mono text-[11px]">
                      {row.device_id}
                    </div>
                  </>
                ) : (
                  <span className="text-text-primary mono">{row.device_id}</span>
                )}
              </td>
              <td className="px-3 py-2.5 text-text-secondary">
                {row.room_name ?? "—"}
              </td>
              <PctCell pcts={row.video} pct="p50" threshold={VIDEO_THRESHOLD} />
              <PctCell pcts={row.video} pct="p75" threshold={VIDEO_THRESHOLD} />
              <PctCell pcts={row.video} pct="p90" threshold={VIDEO_THRESHOLD} />
              <PctCell pcts={row.video} pct="p99" threshold={VIDEO_THRESHOLD} />
              <td className="px-3 py-2.5 text-right num text-text-tertiary">
                {row.video.count.toLocaleString()}
              </td>
              <PctCell pcts={row.audio} pct="p50" threshold={AUDIO_THRESHOLD} />
              <PctCell pcts={row.audio} pct="p75" threshold={AUDIO_THRESHOLD} />
              <PctCell pcts={row.audio} pct="p90" threshold={AUDIO_THRESHOLD} />
              <PctCell pcts={row.audio} pct="p99" threshold={AUDIO_THRESHOLD} />
              <td className="px-5 md:px-6 py-2.5 text-right num text-text-tertiary">
                {row.audio.count.toLocaleString()}
              </td>
            </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
