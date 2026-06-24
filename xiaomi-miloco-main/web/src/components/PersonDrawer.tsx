/**
 * 家人详情抽屉。
 * - 创建模式：新增家人（仅名字 + 家庭角色）
 * - 编辑模式：改名 / 删（二次确认）/ 让它认识她（启动 EnrollFlow）
 */

import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import type { PerceptionCamera, Person } from "@/lib/types";
import { createPerson, deletePerson, updatePerson } from "@/api";
import { PersonAvatar } from "@/components/PersonAvatar";
import { useEscClose } from "@/hooks/useEscClose";
import { IconCheck, IconX } from "@/lib/icons";
import { EnrollFlow } from "./EnrollFlow";
import { toast } from "./Toast";

interface Props {
  person: Person | null; // null = 新增模式
  open: boolean;
  // 打开即直接进入身份录入（成员档案头部「录入身份」入口用）；仅对未录入成员生效。
  startEnrolling?: boolean;
  cameras: PerceptionCamera[];
  onClose: () => void;
  onChanged: () => void;
}

export function PersonDrawer({
  person,
  open,
  startEnrolling = false,
  cameras,
  onClose,
  onChanged,
}: Props) {
  const { t } = useTranslation();
  const [name, setName] = useState("");
  const [role, setRole] = useState("");
  const [editing, setEditing] = useState(false);
  const [enrolling, setEnrolling] = useState(false);
  const [confirmingDel, setConfirmingDel] = useState(false);
  const [busy, setBusy] = useState(false);
  // submit/delete 跑期间挡关闭:scrim/ESC/X 都禁,避免 dialog 关掉但 await 还在跑
  // → 成功 reload 时住户已退出看到莫名刷新,失败 toast 又弹到无 dialog 上下文。
  const guardedClose = busy ? () => {} : onClose;
  useEscClose(open && !busy, guardedClose);

  useEffect(() => {
    if (open) {
      setName(person?.name ?? "");
      setRole(person?.role ?? "");
      setEditing(person == null); // 新增模式默认编辑
      // 从档案头部「录入身份 / 补充身份样本」入口打开即进流程；新增模式不触发。
      setEnrolling(!!person && startEnrolling);
      setConfirmingDel(false);
    } else {
      setConfirmingDel(false);
    }
  }, [open, person, startEnrolling]);

  if (!open) return null;

  // 录入态只显示 EnrollFlow 单层，不在它身后再叠一层 PersonDrawer 弹窗。
  // 直达录入（startEnrolling）下取消 / 完成都整体关闭，回到档案面板；
  // 从编辑弹窗进入的则退回编辑弹窗。
  if (enrolling && person) {
    return (
      <EnrollFlow
        person={person}
        cameras={cameras}
        onClose={() => (startEnrolling ? onClose() : setEnrolling(false))}
        onDone={() => {
          setEnrolling(false);
          onChanged();
          if (startEnrolling) onClose();
        }}
      />
    );
  }

  const isNew = person == null;

  const submit = async () => {
    if (!name.trim()) return;
    setBusy(true);
    try {
      if (isNew) {
        await createPerson({ name: name.trim(), role: role.trim() || undefined });
      } else {
        await updatePerson(person.id, {
          name: name.trim(),
          // 发空串 = 显式清空家庭角色；后端按是否带 role 字段区分"未传(不改)"与"传空(清空)"
          role: role.trim(),
        });
      }
      onChanged();
      onClose();
    } catch (e) {
      toast(e instanceof Error ? e.message : t("family.saveFail"), "warn");
    } finally {
      setBusy(false);
    }
  };

  const doDelete = async () => {
    if (!person) return;
    setBusy(true);
    try {
      await deletePerson(person.id);
      onChanged();
      onClose();
    } catch (e) {
      toast(e instanceof Error ? e.message : t("family.deleteFail"), "warn");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-[60] flex items-end md:items-center justify-center bg-black/40"
      onClick={guardedClose}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="person-drawer-title"
        className="w-full max-w-md bg-bg-secondary border border-border rounded-t-2xl md:rounded-xl shadow-sm p-6 anim-in"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <h3
            id="person-drawer-title"
            className="text-title text-text-primary"
          >
            {isNew ? t("family.addPerson") : person.name}
          </h3>
          <button
            type="button"
            onClick={guardedClose}
            disabled={busy}
            className="rounded-full p-1 text-text-secondary hover:text-text-primary disabled:opacity-50"
            aria-label={t("family.close")}
          >
            <IconX />
          </button>
        </div>

        {/* 头像 */}
        {!isNew && (
          <div className="flex justify-center mb-4">
            <PersonAvatar person={person} size={96} />
          </div>
        )}

        {/* 基本信息 / 编辑 */}
        {editing ? (
          <div className="space-y-3 mb-4">
            <Field label={t("family.drawerName")}>
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder={t("family.drawerNamePlaceholder")}
                autoFocus
                className="w-full px-3 py-2 rounded-lg bg-bg-primary border border-border focus:border-brand-primary focus:outline-none text-text-primary"
              />
            </Field>
            <Field label={t("family.drawerRole")}>
              <input
                value={role}
                onChange={(e) => setRole(e.target.value)}
                placeholder={t("family.drawerRolePlaceholder")}
                className="w-full px-3 py-2 rounded-lg bg-bg-primary border border-border focus:border-brand-primary focus:outline-none text-text-primary"
              />
            </Field>
          </div>
        ) : (
          person && (
            <div className="text-center mb-4">
              <div className="text-text-primary">{person.name}</div>
              {person.role && (
                <div className="text-caption text-text-secondary">
                  {person.role}
                </div>
              )}
            </div>
          )
        )}

        {/* 删除二次确认态 */}
        {confirmingDel && (
          <div className="rounded-lg bg-error-bg border border-error p-3 mb-3">
            <div className="text-error text-center mb-2.5">
              {t("family.confirmDeletePerson", { name: person?.name })}
            </div>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setConfirmingDel(false)}
                disabled={busy}
                className="flex-1 py-2 rounded-lg bg-bg-secondary border border-border text-text-primary disabled:opacity-60"
              >
                {t("family.cancel")}
              </button>
              <button
                type="button"
                onClick={doDelete}
                disabled={busy}
                className="flex-1 py-2 rounded-lg bg-error text-white hover:opacity-90 disabled:opacity-60"
              >
                {busy ? t("family.deleting") : t("family.confirmDelete")}
              </button>
            </div>
          </div>
        )}

        {/* 动作按钮 */}
        {!confirmingDel && (
          <div className="flex flex-col gap-2">
            {editing ? (
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => {
                    if (isNew) {
                      onClose();
                    } else {
                      // 退出编辑态时把 name/role 回滚到 person 当前值，
                      // 避免下次再点"改名"看到上次未保存的脏值
                      setName(person?.name ?? "");
                      setRole(person?.role ?? "");
                      setEditing(false);
                    }
                  }}
                  className="flex-1 py-2 rounded-lg bg-bg-primary border border-border text-text-secondary"
                >
                  {t("family.cancel")}
                </button>
                <button
                  type="button"
                  onClick={submit}
                  disabled={!name.trim() || busy}
                  className="flex-1 py-2 rounded-lg bg-brand-primary text-white hover:bg-brand-accent disabled:opacity-60"
                >
                  <IconCheck className="inline mr-1" />
                  {busy ? t("family.saving") : t("family.save")}
                </button>
              </div>
            ) : (
              !isNew && (
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => setEditing(true)}
                    className="flex-1 py-2 rounded-lg bg-bg-primary border border-border text-text-secondary hover:text-text-primary"
                  >
                    {t("family.rename")}
                  </button>
                  <button
                    type="button"
                    onClick={() => setConfirmingDel(true)}
                    className="flex-1 py-2 rounded-lg bg-bg-primary border border-border text-error hover:bg-error-bg"
                  >
                    {t("family.delete")}
                  </button>
                </div>
              )
            )}
          </div>
        )}

      </div>
    </div>
  );
}

function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <div className="text-caption text-text-secondary mb-1">{label}</div>
      {children}
    </div>
  );
}
