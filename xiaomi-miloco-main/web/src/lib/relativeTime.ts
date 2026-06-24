/**
 * 把 ISO 时间转成住户友好的相对值。
 * 规则：
 *   <1 分钟  → "刚刚"
 *   <60 分钟 → "X 分钟前"
 *   今天    → "HH:MM"
 *   昨天    → "昨天 HH:MM"
 *   更早    → "M 月 D 日"(同年)/ "YYYY 年 M 月 D 日"(跨年)
 *
 * 文案走 i18n `time.*` 域(zh/en JSON)，加语言只需补 JSON、不动这里的逻辑。
 * 中文模板与历史输出逐字一致(测试守此契约)。月份名走 Intl，随 i18n.language 本地化。
 */
import i18n from "@/i18n";

// 本地化短月名(en→"Dec"、ja→"12月"…)，供 dateMD/dateYMD 的 {{mon}} 用;
// 中文模板用 {{m}} 数字、忽略 {{mon}}。
function monShort(d: Date): string {
  return new Intl.DateTimeFormat(i18n.language || "en", {
    month: "short",
  }).format(d);
}

export function relativeTime(
  input: string | number,
  now: Date = new Date(),
): string {
  const t = new Date(input);
  const diffMs = now.getTime() - t.getTime();
  const diffMin = Math.floor(diffMs / 60000);

  if (diffMin < 1) return i18n.t("time.justNow");
  if (diffMin < 60) return i18n.t("time.minAgo", { n: diffMin });

  const sameDay =
    t.getFullYear() === now.getFullYear() &&
    t.getMonth() === now.getMonth() &&
    t.getDate() === now.getDate();
  const hhmm = `${pad(t.getHours())}:${pad(t.getMinutes())}`;
  if (sameDay) return hhmm;

  const yesterday = new Date(now);
  yesterday.setDate(now.getDate() - 1);
  const isYesterday =
    t.getFullYear() === yesterday.getFullYear() &&
    t.getMonth() === yesterday.getMonth() &&
    t.getDate() === yesterday.getDate();
  if (isYesterday) return i18n.t("time.yesterdayAt", { time: hhmm });
  // 跨年时显式带年份:1 月 2 日看到去年 12 月 30 日只显"12 月 30 日"会让住户
  // 误以为是当年同月日(尤其 rule_logs 不带 24h cap 时跨年事件能露出)。
  if (t.getFullYear() !== now.getFullYear()) {
    return i18n.t("time.dateYMD", {
      y: t.getFullYear(),
      m: t.getMonth() + 1,
      d: t.getDate(),
      mon: monShort(t),
    });
  }
  return i18n.t("time.dateMD", {
    m: t.getMonth() + 1,
    d: t.getDate(),
    mon: monShort(t),
  });
}

function pad(n: number) {
  return n < 10 ? `0${n}` : `${n}`;
}

/**
 * 智能时间标签(activity feed 左栏用):
 *   今天    → "今天 HH:mm:ss"
 *   昨天    → "昨天 HH:mm:ss"
 *   跨日    → "YYYY/MM/DD HH:mm:ss"(统一带年份,斜杠分隔)
 *
 * 跟 relativeTime 的相对值不同 — 这个返回绝对时间点,更适合查事件时间.
 */
export function smartTimeLabel(
  input: string | number,
  now: Date = new Date(),
): string {
  const { time, date } = smartTimeParts(input, now);
  return date ? `${date} ${time}` : time;
}

/**
 * 双行版本:时间 / 日期分开,供 ActivityFeed 左栏上下两行布局用.
 *   今天    → { time: "HH:mm:ss", date: "今天" }
 *   昨天    → { time: "HH:mm:ss", date: "昨天" }
 *   跨日    → { time: "HH:mm:ss", date: "YYYY/MM/DD" }(统一带年份,斜杠分隔)
 *
 * 用户体验考虑:即使是今天的事件,左栏第二行也显 "今天" 而非空白 —
 * 一来跟非今日事件的双行布局保持高度对齐(否则今天行只 1 行高,跨日行 2 行高,
 * 列表节奏跳),二来"今天/昨天"明确告诉用户具体相对位置.超出昨天统一 YYYY/MM/DD,
 * 用斜杠跟 HH:mm:ss 的冒号视觉权重区分;不显"周X"(用户回看需要精确日期点).
 */
export function smartTimeParts(
  input: string | number,
  now: Date = new Date(),
): { time: string; date: string } {
  const d = new Date(input);
  const today0 = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
  const d0 = new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime();
  const daysDiff = Math.round((today0 - d0) / 86400000);

  const time = `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
  if (daysDiff === 0) return { time, date: i18n.t("time.today") };
  if (daysDiff === 1) return { time, date: i18n.t("time.yesterday") };
  // 跨日统一 YYYY/MM/DD — 用斜杠分隔符,跟 HH:mm:ss 的冒号视觉权重区分(避免连续短横
  // 让两行同看像"两段破折号").同年也带年份,避免"今年 6 月" vs "去年 6 月"无差别.
  const mo = pad(d.getMonth() + 1);
  const day = pad(d.getDate());
  return { time, date: `${d.getFullYear()}/${mo}/${day}` };
}
