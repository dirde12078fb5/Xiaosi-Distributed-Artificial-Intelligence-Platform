/**
 * 家庭切换器（v3 Mi Console 视觉）
 *
 * 视觉规格：48px 高有边框按钮，左侧房子图标 + 家庭名，右侧「切换」hint + chevron。
 * 视觉规格见 knowledge/07-design/component-patterns.md。
 *
 * `homes` 来自 backend `/api/miot/scope/homes`（米家账号下多家庭 scope 接入范围全集），
 * `onSwitch` 触发 PUT `/api/miot/scope/homes` 切换 in_use 标记。单家账号下 `homes`
 * 长度 = 1 时按钮不展开下拉(光标 default + title 提示"当前账号下只有一个家庭")。
 */

import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import type { HomeId } from "@/lib/types";
import { useEscClose } from "@/hooks/useEscClose";

interface Props {
  currentHomeId: HomeId;
  homes: { id: HomeId; name: string }[];
  /** 切换家庭。当前 homes 只有一项时不会被触发。 */
  onSwitch?: (id: HomeId) => void;
}

export function HomeSwitcher({ currentHomeId, homes, onSwitch }: Props) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  // ESC 关闭 listbox,跟仓内其它弹层(MiotBindDialog / EnrollFlow / PersonDrawer
  // / AccountMenu) a11y 行为对齐。
  useEscClose(open, () => setOpen(false));
  // 点外面收起 —— useEffect **必须**在所有 early return 之前调用,React Hooks
  // rule 要求每次渲染调用相同顺序/数量的 hook。homes 由 N→[] 闪一下时若 hook
  // 在 early return 之后,这一帧 hook 数从 3 (useState+useRef+useEffect) 退到 2
  // (useState+useRef+提前 return) → 下一帧 homes 重新有值 hook 数恢复 3,React
  // 抛 `Rendered fewer hooks than expected` 整个 App 树白屏。父级已 gate
  // `miot.bound && currentHome` 但解绑 OAuth 那一帧 scopeHomes 由 N 变 [] 而
  // status.miot.bound 还没 reload, HomeSwitcher 仍可能拿到 homes=[]。
  useEffect(() => {
    if (!open) return;
    const onDoc = (e: MouseEvent) => {
      if (!ref.current?.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, [open]);

  const current = homes.find((h) => h.id === currentHomeId) ?? homes[0];
  const onlyOne = homes.length <= 1;
  // homes 空（账号刚解绑米家 / scope/homes 没返回）时不渲染——避免按钮显示空名字。
  // 父组件（App.tsx）已在 `miot?.bound && currentHome` 时才挂 HomeSwitcher，
  // 这条防御兜底让其它调用方不需要重复 gate。
  if (!current) return null;

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => !onlyOne && setOpen((v) => !v)}
        aria-haspopup={onlyOne ? undefined : "listbox"}
        aria-expanded={onlyOne ? undefined : open}
        title={onlyOne ? t("account.switchHomeOnlyOne") : t("account.switchHome")}
        className={`group inline-flex items-baseline gap-2 min-w-0 ${
          onlyOne ? "cursor-default" : ""
        }`}
      >
        {/* 字号 text-body(14)而非原 text-page-title(20):design-tokens §3 黄金
            阶梯规定 caption/body/title/display 四档,Sidebar 顶 Miloco 是 text-title
            (16);TopBar 家名作为次级 anchor 应小于品牌字。font-semibold 把视觉权
            重补回来,避免 14 太弱。 */}
        <span className="text-body font-semibold text-text-primary truncate">
          {current.name}
        </span>
        {!onlyOne && (
          <span className="text-caption shrink-0 transition-colors text-text-tertiary group-hover:text-brand-primary">
            {t("account.switch")}
          </span>
        )}
      </button>

      {open && !onlyOne && (
        <div
          role="listbox"
          aria-label={t("account.switchHomeListLabel")}
          className="text-body absolute left-0 top-full mt-1 z-20 min-w-[200px] rounded-lg bg-bg-secondary border border-border shadow-md overflow-hidden"
        >
          {homes.map((h) => (
            <button
              key={h.id}
              type="button"
              role="option"
              aria-selected={h.id === currentHomeId}
              onClick={() => {
                onSwitch?.(h.id);
                setOpen(false);
              }}
              className={`w-full text-left px-3 py-2 transition-colors ${
                h.id === currentHomeId
                  ? "bg-brand-soft text-brand-primary"
                  : "text-text-primary hover:bg-bg-tertiary"
              }`}
            >
              {h.name}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
