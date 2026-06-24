/**
 * 主题切换 hook —— App 根挂载,跟随 prefers-color-scheme + 持久化用户偏好。
 *
 * 三态模型：
 *  - "auto"：跟随系统 prefers-color-scheme（默认）
 *  - "light"：强制明亮
 *  - "dark"：强制暗色
 *
 * effective 永远是 "light" | "dark"——用于决定显示太阳还是月亮图标。
 *
 * 跨组件同步：写入时 dispatch 自定义事件，所有挂着该 hook 的组件同步刷。
 */

import { useEffect, useState } from "react";

const KEY = "web:theme";
const EVENT = "miloco-theme-change";

export type ThemeChoice = "auto" | "light" | "dark";

function read(): ThemeChoice {
  if (typeof window === "undefined") return "auto";
  const v = localStorage.getItem(KEY);
  if (v === "light" || v === "dark") return v;
  return "auto";
}

function apply(t: ThemeChoice) {
  if (typeof window === "undefined") return;
  if (t === "auto") {
    document.documentElement.removeAttribute("data-theme");
    localStorage.removeItem(KEY);
  } else {
    document.documentElement.setAttribute("data-theme", t);
    localStorage.setItem(KEY, t);
  }
  window.dispatchEvent(new Event(EVENT));
}

function computeEffective(t: ThemeChoice): "light" | "dark" {
  if (t === "light" || t === "dark") return t;
  if (typeof window === "undefined") return "light";
  // URL ?theme= 临时覆盖（main.tsx 只设 data-theme 不写 localStorage）：
  // 此时 t==="auto" 但 data-theme 已是 light/dark——以 data-theme 为权威，
  // 否则 toggle icon 会跟实际主题反过来（页面 dark / 图标显示"切换到 dark"）。
  const forced = document.documentElement.getAttribute("data-theme");
  if (forced === "light" || forced === "dark") return forced;
  return window.matchMedia("(prefers-color-scheme: dark)").matches
    ? "dark"
    : "light";
}

export function useTheme(): {
  theme: ThemeChoice;
  effective: "light" | "dark";
  setTheme: (t: ThemeChoice) => void;
  toggle: () => void;
} {
  const [theme, setThemeState] = useState<ThemeChoice>(read);
  const [effective, setEffective] = useState<"light" | "dark">(() =>
    computeEffective(read()),
  );

  useEffect(() => {
    const sync = () => {
      const t = read();
      setThemeState(t);
      setEffective(computeEffective(t));
    };
    // 同 tab 内自定义事件 + 跨 tab storage 事件 + 系统主题变化
    window.addEventListener(EVENT, sync);
    window.addEventListener("storage", sync);
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    mq.addEventListener("change", sync);
    return () => {
      window.removeEventListener(EVENT, sync);
      window.removeEventListener("storage", sync);
      mq.removeEventListener("change", sync);
    };
  }, []);

  const setTheme = (t: ThemeChoice) => {
    apply(t);
    setThemeState(t);
    setEffective(computeEffective(t));
  };

  const toggle = () => {
    setTheme(effective === "dark" ? "light" : "dark");
  };

  return { theme, effective, setTheme, toggle };
}
