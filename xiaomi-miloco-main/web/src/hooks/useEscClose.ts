/**
 * dialog/抽屉的 Esc 键关闭——a11y 标准。
 *
 * 用法：useEscClose(open, onClose)
 *
 * **栈语义**：多个 dialog 同时打开时，Esc 只关闭"最后打开的那个"——
 * 而不是同时关掉所有层。靠模块级 stack 维护打开顺序，最后注册的 close
 * handler 处理 Esc 后即结束（stopImmediatePropagation）。
 */

import { useEffect, useRef } from "react";

// 用稳定的 ref 对象作 stack 元素，handler 通过 ref 取最新闭包；
// effect deps 只放 [open]，避免 onClose 引用每帧变化导致 cleanup→push
// 把后打开的层翻到栈底（破坏"Esc 只关最后那个"承诺）。
type Slot = { onClose: () => void };
const stack: Slot[] = [];
let listenerAttached = false;

function ensureListener() {
  if (listenerAttached) return;
  listenerAttached = true;
  window.addEventListener("keydown", (e) => {
    if (e.key !== "Escape") return;
    const top = stack[stack.length - 1];
    if (top) {
      e.stopPropagation();
      e.stopImmediatePropagation();
      top.onClose();
    }
  });
}

export function useEscClose(open: boolean, onClose: () => void) {
  const slotRef = useRef<Slot>({ onClose });
  // 每次 render 把最新闭包写到 ref，handler 总能拿到最新版本。
  slotRef.current.onClose = onClose;

  useEffect(() => {
    if (!open) return;
    ensureListener();
    const slot = slotRef.current;
    stack.push(slot);
    return () => {
      const i = stack.lastIndexOf(slot);
      if (i >= 0) stack.splice(i, 1);
    };
  }, [open]);
}
