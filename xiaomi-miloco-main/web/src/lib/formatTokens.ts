// 用量数字的住户友好格式化。三处用量组件（UsageTodayOverview /
// UsageBreakdownTable / UsageTimelineChart）必须共用一份，否则同一笔
// tokens 在不同卡片显示精度不一会触发"是不是数字跳了"的视觉抖动。
//
// 阈值与保留位数：
//   < 1k       → 整数（"850"）
//   1k - 1M    → "X.Xk"（保留 1 位小数）
//   ≥ 1M       → "X.XXM"（保留 2 位小数，避免精度损失）

export function humanTokens(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(2)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}k`;
  return `${Math.round(n)}`;
}

// 极紧空间下的更短格式（图表轴标），同阈值但省一位小数。
export function humanTokensShort(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(0)}k`;
  return `${Math.round(n)}`;
}
