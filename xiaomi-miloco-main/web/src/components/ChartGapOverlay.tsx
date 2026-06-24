/**
 * 时序 chart 公共组件:在 densify 填出来的无数据 bucket 上画斜纹底色,
 * 一眼区分"无数据"与"数据为 0"。
 *
 * 用法:在每个 Perf*Chart 的 SVG 内,最底层(y 网格/折线之前)render
 * <ChartGapOverlay ... />。pattern defs 跟 rects 一起返回, 调用方一次 mount。
 *
 * pattern id 在每个 SVG 内部生效(SVG xml namespace 隔离),不同 chart
 * 同 id 不冲突。
 */
import { Fragment } from "react";

const PATTERN_ID = "chart-gap-stripes";

interface Props {
  regions: { startIdx: number; endIdx: number }[];
  xSvgAt: (i: number) => number;
  n: number;
  svgW: number;
  padL: number;
  padR: number;
  padT: number;
  padB: number;
  chartH: number;
}

export function ChartGapOverlay({
  regions, xSvgAt, n, svgW, padL, padR, padT, padB, chartH,
}: Props) {
  if (regions.length === 0) return null;
  return (
    <Fragment>
      <defs>
        <pattern
          id={PATTERN_ID}
          patternUnits="userSpaceOnUse"
          width="10"
          height="10"
          patternTransform="rotate(45)"
        >
          <line
            x1="0" y1="0" x2="0" y2="10"
            className="stroke-text-tertiary"
            strokeWidth="4"
            opacity="0.35"
          />
        </pattern>
      </defs>
      {regions.map((g) => {
        // 边界对齐到相邻"有数据 bucket"中心,跟折线起止点贴齐,消除半个 bucket
        // 的视觉空隙。gap 两侧的数据点本身处于斜纹边缘上,圆点/折线端点不被遮。
        const leftEdge = g.startIdx > 0 ? xSvgAt(g.startIdx - 1) : padL;
        const rightEdge = g.endIdx + 1 < n ? xSvgAt(g.endIdx + 1) : svgW - padR;
        const x1 = Math.max(padL, leftEdge);
        const x2 = Math.min(svgW - padR, rightEdge);
        return (
          <rect
            key={`gap-${g.startIdx}`}
            x={x1}
            y={padT}
            width={x2 - x1}
            height={chartH - padT - padB}
            fill={`url(#${PATTERN_ID})`}
          />
        );
      })}
    </Fragment>
  );
}
