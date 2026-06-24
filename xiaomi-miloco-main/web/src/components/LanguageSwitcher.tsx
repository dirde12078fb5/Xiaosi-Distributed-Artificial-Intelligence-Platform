/** 语言切换器（中文 / English）—— 复用通用 Segmented，放 TopBar 操作区。 */
import { useTranslation } from "react-i18next";
import { Segmented } from "./Segmented";
import type { Lang } from "@/i18n";

export function LanguageSwitcher() {
  const { t, i18n } = useTranslation();
  const cur: Lang = i18n.language === "en" ? "en" : "zh";
  return (
    <Segmented<Lang>
      ariaLabel={t("lang.label")}
      value={cur}
      onChange={(v) => {
        if (v === cur) return;
        // 整页 reload：部分文案（设备状态/属性名）在取数映射时按当时语言烘焙进
        // 数据对象，纯组件重渲染翻不动；reload 触发重新拉取，整页语言一致。
        // localStorage 已由 i18n 的 languageChanged 回调写入，reload 后读到新语言。
        i18n.changeLanguage(v).then(() => window.location.reload());
      }}
      options={[
        { key: "zh", label: t("lang.zh") },
        { key: "en", label: t("lang.en") },
      ]}
    />
  );
}
