/**
 * 极简 Toast——替代 window.alert。模块级 emitter，全局 Provider 渲染。
 *
 * 用法：
 *   import { toast } from "./Toast";
 *   toast("已替你关上厨房灯");
 *   toast("摄像头连不上了", "warn");
 *
 * tone：info（默认）/ ok / warn / danger，对应 §零.2 严重度色板。
 *
 * z-index:z-[100]——必须高于所有 modal stack(普通 dialog z-[60],例如
 * MiotBindDialog / PersonDrawer / EnrollFlow /
 * LivePlayer expanded)。z-[70] / z-[80] 是 design-tokens.md 给未来双层
 * modal 预留的层位,本仓当前无活跃组件占用。否则在 dialog onConfirm catch
 * 抛 toast 时被 modal scrim 盖住住户看不见,业务错完全静默。新增 modal
 * 层时不要超过 z-[99]。
 */

import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { IconX } from "@/lib/icons";

export type ToastTone = "info" | "ok" | "warn" | "danger";

interface ToastItem {
  id: number;
  text: string;
  tone: ToastTone;
}

type Listener = (t: ToastItem) => void;
const listeners: Listener[] = [];
let nextId = 1;

// 同 text + tone 的 toast 在 1.5s 内不重复推 —— 防住户连点 cta 触发 toast 堆叠
// 遮挡 StatusRibbon。tone 不同视为不同消息（如 ok / warn 切换需要看到）。
// sweep：每次 set 前清掉过期 entry，避免 dynamic toast（含住户名/设备名/错误
// message）在长时间运行的 SPA 里让 Map 单调累积。
const RECENT_DEDUP_MS = 1500;
const recentByKey = new Map<string, number>();

export function toast(text: string, tone: ToastTone = "info") {
  const key = `${tone}:${text}`;
  const now = Date.now();
  const last = recentByKey.get(key);
  if (last !== undefined && now - last < RECENT_DEDUP_MS) return;
  recentByKey.set(key, now);
  // setTimeout 自删 entry,省掉每次 O(n) sweep。住户长时间挂面板时 dedup
  // 自然过期不积累。
  setTimeout(() => {
    if (recentByKey.get(key) === now) recentByKey.delete(key);
  }, RECENT_DEDUP_MS);
  const item: ToastItem = { id: nextId++, text, tone };
  for (const l of listeners) l(item);
}

const toneCls: Record<ToastTone, string> = {
  info: "bg-info-bg text-info border-info",
  ok: "bg-success-bg text-success border-success",
  warn: "bg-warning-bg text-warning border-warning",
  danger: "bg-error-bg text-error border-error",
};

const AUTO_DISMISS_MS = 3500;

export function ToastHost() {
  const { t: tr } = useTranslation();
  const [items, setItems] = useState<ToastItem[]>([]);

  useEffect(() => {
    const timers = new Map<number, ReturnType<typeof setTimeout>>();
    const onPush: Listener = (t) => {
      // 队列 cap 5 条防长跑 SPA 频繁 burst 累积 DOM(3.5s 自动消逝兜底,但短窗
      // 内可能堆几十条)。新进的留,最旧 2 条挤出。
      setItems((xs) => [...xs, t].slice(-5));
      const id = setTimeout(() => {
        setItems((xs) => xs.filter((x) => x.id !== t.id));
        timers.delete(t.id);
      }, AUTO_DISMISS_MS);
      timers.set(t.id, id);
    };
    listeners.push(onPush);

    // pop 跨 reload 待显消息（典型场景：切家失败时 toast 来不及显 reload 已开始
    // 卸载 ToastHost；写入 sessionStorage，mount 后 pop 出来显示）。
    try {
      const raw = sessionStorage.getItem("miloco_pending_toast");
      if (raw) {
        sessionStorage.removeItem("miloco_pending_toast");
        // 运行时校验：sessionStorage 来源不可信（住户手改 / 浏览器扩展灌脏数据 /
        // 旧版字段残留）。typeof + tone 白名单兜底,防 `bg-${tone}` 等 dynamic class
        // 拼出非法 token 让 toast 渲染异常或失败。
        const parsed = JSON.parse(raw) as Record<string, unknown>;
        const text = parsed.text;
        const toneRaw = parsed.tone;
        // mapped type 强 exhaustive:ToastTone 将来扩成第 5 个 tone 时,这里漏补
        // 对应 key 编译期 fail (Record<ToastTone,true> 缺 key)。`satisfies readonly
        // ToastTone[]` 只验赋值方向不验穷尽,新增 tone 漏改就只会运行期 fallback。
        const TONES: Record<ToastTone, true> = { info: true, ok: true, warn: true, danger: true };
        const tone: ToastTone =
          typeof toneRaw === "string" && Object.prototype.hasOwnProperty.call(TONES, toneRaw)
            ? (toneRaw as ToastTone)
            : "info";
        if (typeof text === "string" && text.length > 0) {
          // cap 200 防 sessionStorage 被恶意 / bug 写超长字符串让首屏卡渲染。
          // 直接 setItems 不走 toast() listener 间接路径 — 在自己 mount effect
          // 内 toast → forEach listeners 让自己消费的链路绕,可读性差。
          const id = (Date.now() << 1) ^ Math.floor(Math.random() * 1024);
          const t = { id, text: text.slice(0, 200), tone };
          setItems((xs) => [...xs, t].slice(-5));
          const tid = setTimeout(() => {
            setItems((xs) => xs.filter((x) => x.id !== t.id));
            timers.delete(t.id);
          }, AUTO_DISMISS_MS);
          timers.set(t.id, tid);
        }
      }
    } catch {
      /* 清掉损坏的 entry，下次干净 */
      try { sessionStorage.removeItem("miloco_pending_toast"); } catch {/**/}
    }

    return () => {
      const i = listeners.indexOf(onPush);
      if (i >= 0) listeners.splice(i, 1);
      // 卸载时清掉所有未触发的 timer，避免在 unmounted 组件上 setItems。
      for (const id of timers.values()) clearTimeout(id);
      timers.clear();
    };
  }, []);

  if (items.length === 0) return null;
  return (
    <div
      role="region"
      aria-live="polite"
      aria-atomic="false"
      aria-label={tr("common.notification")}
      className="fixed top-4 md:top-6 left-1/2 -translate-x-1/2 z-[100] flex flex-col gap-2 max-w-[90vw] max-h-[40vh] overflow-y-auto pointer-events-none"
    >
      {items.map((t) => (
        <div
          key={t.id}
          className={`anim-in text-caption flex items-center gap-2 px-4 py-2.5 rounded-xl border shadow-md pointer-events-auto ${toneCls[t.tone]}`}
        >
          <span className="flex-1">{t.text}</span>
          <button
            type="button"
            onClick={() => setItems((xs) => xs.filter((x) => x.id !== t.id))}
            className="opacity-70 hover:opacity-100"
            aria-label={tr("common.close")}
          >
            <IconX width={14} height={14} />
          </button>
        </div>
      ))}
    </div>
  );
}
