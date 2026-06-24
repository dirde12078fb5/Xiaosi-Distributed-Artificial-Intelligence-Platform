/**
 * 观察中（候选）聚合面板——家庭 tab 总览第三张卡。
 *
 * 把所有成员 + 家庭的候选集中到一处审阅：每行露出内容 + 归属（subjectName），
 * 点行 → 详情卡确认收下 / 忽略。已达收录条件的排前面。无候选时整卡不渲染，
 * 保持总览平静。候选只在此处出现（成员档案 / 家庭档案不再单列），避免一条
 * 候选在两处重复。
 */

import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import type { HomeEntries, HomeEntry } from "@/lib/types";
import {
  CandidateRow,
  EntryDetailSheet,
  bindCandidateActions,
  useHomeWrite,
} from "./HomeProfileParts";

interface Props {
  data: HomeEntries | undefined;
  onChanged: () => void;
}

export function CandidateReviewPanel({ data, onChanged }: Props) {
  const { t } = useTranslation();
  const run = useHomeWrite(onChanged);
  const [selected, setSelected] = useState<HomeEntry | null>(null);

  const ready = useMemo(() => new Set(data?.readyToPromote ?? []), [data]);
  const candidates = useMemo(() => {
    const list = [...(data?.candidates ?? [])];
    // 已达收录条件的排前面——它们最该被处理。
    return list.sort((a, b) => Number(ready.has(b.id)) - Number(ready.has(a.id)));
  }, [data, ready]);

  // 无候选 → 不渲染（含初次加载 data 未到时），让总览保持平静。
  if (candidates.length === 0) return null;

  return (
    <section
      className="rounded-xl bg-bg-secondary border border-border shadow-sm anim-in"
      aria-labelledby="candidate-review-title"
    >
      <div className="px-5 pt-4 pb-1">
        <h2
          id="candidate-review-title"
          className="text-title text-text-primary inline-flex items-baseline gap-2"
        >
          {t("family.candidateTitle")}
          <span className="text-caption-mono text-text-tertiary font-normal num">
            {t("family.knowledgeCount", { count: candidates.length })}
          </span>
        </h2>
      </div>
      <p className="px-5 pb-2 text-caption text-text-tertiary">
        {t("family.candidateHint")}
      </p>

      <div className="px-5 pb-4">
        <div className="divide-y divide-border">
          {candidates.map((e) => (
            <CandidateRow key={e.id} entry={e} onOpen={() => setSelected(e)} />
          ))}
        </div>
      </div>

      {selected && (
        <EntryDetailSheet
          entry={selected}
          onClose={() => setSelected(null)}
          {...bindCandidateActions(run, selected)}
        />
      )}
    </section>
  );
}
