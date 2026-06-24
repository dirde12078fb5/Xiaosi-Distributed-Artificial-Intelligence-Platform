/**
 * 家人圆形头像:统一组件——所有家人头像位都走它。
 *
 * - 已录入(faceEnrolled=true)且主 backend 起着:拉首张 face 样本作 <img>
 * - 否则:淡彩色底(paletteFor(person.avatarHue))+ 白色 IconPerson 填充
 *
 * 淡彩色由 personPalette 的 6 套预设决定,通过 person.avatarHue 索引:
 *   listPersons:i % 6(按返回列表序,跨 reload 稳定)
 *   createPerson:Math.random() % 6(本地态,下次 listPersons reload 时被 i % 6 覆盖)
 *
 * 路由迁移:已从独立 register_server(``/identity/*``)迁到主 backend(``/api/identity/*``)。
 */
import { useEffect, useState } from "react";
import type { Person } from "@/lib/types";
import { IconCheck, IconPerson } from "@/lib/icons";
import { paletteFor } from "@/lib/personPalette";
import { authHeaders } from "@/api/register";

interface Props {
  person: Person;
  /** 直径 px */
  size?: number;
  /** 已采集身份时，右下角挂一个 success 对勾角标（未采集则不挂，靠"无角标"区分）。 */
  badge?: boolean;
}

interface SampleList {
  face?: { filename: string }[];
}

export function PersonAvatar({ person, size = 28, badge = false }: Props) {
  const [src, setSrc] = useState<string | null>(null);
  const enrolled = person.faceEnrolled;
  const iconSize = Math.round(size * 0.58);
  const palette = paletteFor(person.avatarHue);
  const badgeSize = Math.max(14, Math.round(size * 0.34));

  useEffect(() => {
    if (!enrolled) {
      setSrc(null);
      return;
    }
    let cancelled = false;
    let objectUrl: string | null = null;
    (async () => {
      try {
        const r = await fetch(`/api/identity/persons/${person.id}/samples`, {
          cache: "no-store",
          headers: authHeaders(),
        });
        if (!r.ok) return;
        const json = (await r.json()) as { data?: SampleList };
        const filename = json.data?.face?.[0]?.filename;
        if (!filename || cancelled) return;
        // 不能直接 <img src="/api/...">:/sample/{tier}/{filename} 端点要求
        // Bearer token,而 <img> 元素没法挂 Authorization header。dev 下走
        // vite proxy::attachAuth 注入还能跑;prod 下后端直发 SPA,前端用 Bearer
        // header 鉴权,<img> 直接拿不到 → 401 → 头像变色块。改成 fetch + blob
        // URL,统一 authHeaders 注入,两环境一致。
        const imgRes = await fetch(
          `/api/identity/persons/${person.id}/sample/a/${filename}`,
          { headers: authHeaders() },
        );
        if (!imgRes.ok || cancelled) return;
        const blob = await imgRes.blob();
        if (cancelled) return;
        objectUrl = URL.createObjectURL(blob);
        setSrc(objectUrl);
      } catch {
        /* 主 backend 未起时保留图标占位 */
      }
    })();
    return () => {
      cancelled = true;
      // blob URL 必须显式 revoke,否则 GC 不回收,长跑页面会泄。同时把 src state
      // 切回 null,避免 <img> 仍引用已 revoke 的 URL — Chrome 偶发 zoom/repaint
      // 触发 blob 重 fetch 时会拿到 404 让头像变占位。
      if (objectUrl) {
        const url = objectUrl;
        setSrc((cur) => (cur === url ? null : cur));
        URL.revokeObjectURL(url);
      }
    };
  }, [person.id, enrolled]);

  return (
    <span
      className="relative inline-flex shrink-0"
      style={{ width: size, height: size }}
      aria-hidden
    >
      <span
        className="rounded-full w-full h-full overflow-hidden flex items-center justify-center"
        style={{ background: src ? "var(--color-bg-tertiary)" : palette.bg }}
      >
        {src ? (
          <img
            src={src}
            alt=""
            className="w-full h-full object-cover"
            onError={() => setSrc(null)}
          />
        ) : (
          <IconPerson
            width={iconSize}
            height={iconSize}
            className="text-white"
          />
        )}
      </span>
      {badge && enrolled && (
        <span
          className="absolute bottom-0 right-0 rounded-full bg-success flex items-center justify-center border-2 border-bg-secondary"
          style={{ width: badgeSize, height: badgeSize }}
        >
          <IconCheck
            width={Math.round(badgeSize * 0.66)}
            height={Math.round(badgeSize * 0.66)}
            className="text-white"
            strokeWidth={2.4}
          />
        </span>
      )}
    </span>
  );
}
