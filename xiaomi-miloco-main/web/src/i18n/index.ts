/**
 * i18n 初始化 —— main.tsx 在 render 前 side-effect 导入。
 *
 * 语言态由 i18next 自身管理,偏好持久化到 localStorage["web:lang"](与 web:theme
 * 对齐)。默认中文,可选英文;缺词回退到中文。
 *
 * 非组件模块(api/real.ts、lib/relativeTime.ts)直接 `import i18n from "@/i18n"`
 * 用 i18n.t(...) / i18n.language —— i18next 的 t 在 React 组件外同样可用。
 */
import i18n from "i18next";
import { initReactI18next } from "react-i18next";

// 译文按域拆分到 locales/{zh,en}/*.json,用 Vite glob 自动合并 —— 新增域文件
// 无需改本文件。每个域文件形如 { "<域>": { ...keys } },顶层 key 互不重叠。
function mergeLocale(mods: Record<string, unknown>): Record<string, unknown> {
  return Object.assign(
    {},
    ...Object.values(mods).map((m) => (m as { default: unknown }).default ?? m),
  );
}
const zh = mergeLocale(
  import.meta.glob("./locales/zh/*.json", { eager: true }),
);
const en = mergeLocale(
  import.meta.glob("./locales/en/*.json", { eager: true }),
);

export const LANG_KEY = "web:lang";
export type Lang = "zh" | "en";

function readLang(): Lang {
  // 测试(node 环境)给的是 window 桩、没有 localStorage——用 typeof 守住,
  // 缺失时回退中文(测试默认走 zh 路径)。
  if (typeof localStorage === "undefined") return "zh";
  const v = localStorage.getItem(LANG_KEY);
  return v === "en" ? "en" : "zh";
}

i18n.use(initReactI18next).init({
  resources: {
    zh: { translation: zh },
    en: { translation: en },
  },
  lng: readLang(),
  fallbackLng: "zh",
  interpolation: { escapeValue: false },
});

// 切语言 → 持久化 + 同步 <html lang>。初次也设一次。
function syncHtmlLang(lng: string) {
  if (typeof document !== "undefined") {
    document.documentElement.lang = lng === "en" ? "en" : "zh-CN";
  }
}
syncHtmlLang(i18n.language);
i18n.on("languageChanged", (lng) => {
  if (typeof localStorage !== "undefined") localStorage.setItem(LANG_KEY, lng);
  syncHtmlLang(lng);
});

export default i18n;
