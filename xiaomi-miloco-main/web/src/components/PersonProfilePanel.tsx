/**
 * 成员档案面板——家庭 tab 单页上下布局：上方 chip 选中某成员后，此面板就地展开其档案。
 *
 * 头部右侧「录入身份」（未采集时）/「补充身份样本」（已采集）/「编辑」唤起 PersonDrawer
 * 做改名 / 录入身份 / 删除；身份采集状态用头像角标 + 一行文字说明双重表达。
 * 主体按类型分组平静展示正式记忆，点行 → 详情卡看/改/删（候选已集中到总览「观察中」卡）。
 */

import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import type { HomeEntries, HomeEntry, Person } from "@/lib/types";
import { PersonAvatar } from "@/components/PersonAvatar";
import {
  AddEntryForm,
  EntryDetailSheet,
  EntryRow,
  MEMBER_TYPE_ORDER,
  typeLabel,
  addHomeEntry,
  bindEntryActions,
  isMemberType,
  useHomeWrite,
} from "./HomeProfileParts";

interface Props {
  person: Person;
  entries: HomeEntries | undefined;
  loading: boolean;
  onEdit: () => void;
  onEnroll: () => void;
  onChanged: () => void;
}

export function PersonProfilePanel({
  person,
  entries,
  loading,
  onEdit,
  onEnroll,
  onChanged,
}: Props) {
  const { t } = useTranslation();
  const run = useHomeWrite(onChanged);
  // 当前在详情卡里查看的正式条目（候选已集中到总览「观察中」聚合卡，不在此面板）。
  const [selected, setSelected] = useState<HomeEntry | null>(null);

  const profile = useMemo(
    () =>
      (entries?.profile ?? []).filter(
        (e) => e.subjectId === person.id && isMemberType(e.type),
      ),
    [entries, person.id],
  );

  const groups = MEMBER_TYPE_ORDER.map((type) => ({
    type,
    items: profile.filter((e) => e.type === type),
  })).filter((g) => g.items.length > 0);

  const empty = !loading && profile.length === 0;

  // 选中成员后单独成卡，列在「家庭成员」选择条下方。
  return (
    <>
      <section
        aria-labelledby="member-profile-title"
        className="rounded-xl bg-bg-secondary border border-border shadow-sm anim-in"
      >
        <div>
        {/* 头部——头像 + 名字(家庭角色药丸) / 身份状态·特征数；右侧身份与编辑入口。
            移动端竖排（身份在上、操作按钮单独一行），sm 起并排。 */}
        <div className="flex flex-col gap-3 px-5 py-4 border-b border-border sm:flex-row sm:items-center sm:gap-3.5">
          <div className="flex items-center gap-3.5 min-w-0 sm:flex-1">
            <PersonAvatar person={person} size={48} badge />
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2 min-w-0">
                <h3
                  id="member-profile-title"
                  className="text-title text-text-primary truncate"
                >
                  {person.name}
                </h3>
                {person.role && (
                  <span className="shrink-0 text-caption text-text-secondary font-normal px-2 py-0.5 rounded-md bg-bg-tertiary">
                    {person.role}
                  </span>
                )}
              </div>
              <div className="text-caption mt-1.5 flex items-center gap-1.5">
                <span
                  className={`status-dot ${
                    person.faceEnrolled ? "status-dot-ok" : "status-dot-warn"
                  }`}
                />
                <span className="text-text-tertiary">
                  {person.faceEnrolled
                    ? t("family.faceEnrolled")
                    : t("family.faceNotEnrolled")}
                  {profile.length > 0 && (
                    <>
                      {" · "}
                      <span className="num">{profile.length}</span> {t("family.featureCount")}
                    </>
                  )}
                </span>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            {person.faceEnrolled ? (
              <button
                type="button"
                onClick={onEnroll}
                className="text-caption px-3 py-1.5 rounded-md bg-bg-primary border border-border text-text-secondary hover:text-text-primary hover:border-border-strong transition-colors"
              >
                {t("family.memberProfileEnrollMore")}
              </button>
            ) : (
              <button
                type="button"
                onClick={onEnroll}
                className="text-caption px-3 py-1.5 rounded-md bg-brand-soft text-brand-primary border border-transparent hover:bg-brand-primary hover:text-white transition-colors"
              >
                {t("family.memberProfileEnroll")}
              </button>
            )}
            <button
              type="button"
              onClick={onEdit}
              className="text-caption px-3 py-1.5 rounded-md bg-bg-primary border border-border text-text-secondary hover:text-text-primary hover:border-border-strong transition-colors"
            >
              {t("family.edit")}
            </button>
          </div>
        </div>

        {/* 主体：记忆区——单列分组，组间留窄间距、组标题加粗以分清 */}
        <div className="px-5 pt-4 pb-4">
          {loading && !entries ? (
            <div className="text-body text-text-secondary py-10 text-center">
              <span className="inline-flex items-center gap-2">
                <span className="inline-block w-2 h-2 rounded-full bg-text-tertiary animate-pulse" />
                {t("family.loading")}
              </span>
            </div>
          ) : empty ? (
            <div className="text-body text-text-secondary py-10 text-center">
              {t("family.profileEmpty", { name: person.name })}
              <div className="text-caption text-text-tertiary mt-1">
                {t("family.profileEmptyHint")}
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {groups.map((g) => (
                <section key={g.type}>
                  <h4 className="text-caption text-text-tertiary mb-1">
                    {typeLabel(g.type)}
                  </h4>
                  <div className="divide-y divide-border">
                    {g.items.map((e) => (
                      <EntryRow
                        key={e.id}
                        entry={e}
                        onOpen={() => setSelected(e)}
                      />
                    ))}
                  </div>
                </section>
              ))}
            </div>
          )}
        </div>

        {/* 底部：新增记忆 */}
        <div className="px-5 py-4 border-t border-border">
          <AddEntryForm
            types={MEMBER_TYPE_ORDER}
            addLabel={t("family.addEntry")}
            onAdd={(input: { type: HomeEntry["type"]; content: string }) =>
              run(
                () =>
                  addHomeEntry({
                    type: input.type,
                    content: input.content,
                    subjectId: person.id,
                    subjectName: person.name,
                  }),
                t("family.added"),
              )
            }
          />
        </div>
      </div>
      </section>

      {selected && (
        <EntryDetailSheet
          entry={selected}
          onClose={() => setSelected(null)}
          {...bindEntryActions(run, selected)}
        />
      )}
    </>
  );
}
