/**
 * 家人 chip（v3 Mi Console 视觉）
 *
 * 圆形头像 + 名字 + 录入状态（已认识 / 还没认识）。
 */

import { useTranslation } from "react-i18next";
import type { Person } from "@/lib/types";
import { PersonAvatar } from "@/components/PersonAvatar";

interface Props {
  person: Person;
  onClick?: () => void;
  size?: "sm" | "md" | "lg";
}

export function PersonChip({ person, onClick, size = "md" }: Props) {
  const { t } = useTranslation();
  const dim = size === "lg" ? 36 : size === "sm" ? 24 : 28;
  const enrolled = person.faceEnrolled;

  // onClick 不传 → 渲染成 div（不可点 + 无 hover 提色），避免概览页家人 chip
  // 看着像 button 但点了无反馈让住户怀疑系统坏。可点态保留 button + hover。
  const baseCls = "inline-flex items-center gap-2 pl-2 pr-4 py-1 rounded-full bg-bg-secondary border border-border";
  const inner = (
    <>
      <PersonAvatar person={person} size={dim} />
      <span className="flex flex-col items-start leading-tight">
        <span className="text-body text-text-primary leading-[18px]">
          {person.name}
        </span>
        <span
          className={`text-caption ${
            enrolled ? "text-success" : "text-text-tertiary"
          }`}
        >
          {enrolled ? t("family.chipKnown") : t("family.chipUnknown")}
        </span>
      </span>
    </>
  );

  if (!onClick) {
    return <div className={baseCls}>{inner}</div>;
  }
  return (
    <button
      type="button"
      onClick={onClick}
      className={`${baseCls} transition-colors hover:border-border-strong`}
    >
      {inner}
    </button>
  );
}
