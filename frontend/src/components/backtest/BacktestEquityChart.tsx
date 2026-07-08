import type { BacktestEquityPoint } from "@/types/backtest";

interface BacktestEquityChartProps {
  points: BacktestEquityPoint[];
}

export function BacktestEquityChart({ points }: BacktestEquityChartProps) {
  if (points.length < 2) {
    return (
      <div className="rounded-xl border border-dashed border-[var(--border)] bg-[var(--surface)]/20 p-8 text-center text-sm text-[var(--muted)]">
        자산 곡선을 그리려면 2개 이상의 스냅샷 날짜가 필요합니다.
      </div>
    );
  }

  const width = 640;
  const height = 220;
  const padding = { top: 16, right: 16, bottom: 28, left: 44 };
  const innerW = width - padding.left - padding.right;
  const innerH = height - padding.top - padding.bottom;

  const allValues = points.flatMap((p) => [p.portfolio, p.benchmark]);
  const minY = Math.min(...allValues) * 0.98;
  const maxY = Math.max(...allValues) * 1.02;
  const rangeY = maxY - minY || 1;

  const xAt = (index: number) =>
    padding.left + (index / (points.length - 1)) * innerW;
  const yAt = (value: number) =>
    padding.top + innerH - ((value - minY) / rangeY) * innerH;

  const toPath = (key: "portfolio" | "benchmark") =>
    points
      .map((p, i) => `${i === 0 ? "M" : "L"} ${xAt(i).toFixed(1)} ${yAt(p[key]).toFixed(1)}`)
      .join(" ");

  const last = points[points.length - 1];

  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)]/40 p-5">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <h3 className="text-sm font-semibold">자산 곡선 (기준=1.0)</h3>
        <div className="flex gap-4 text-xs text-[var(--muted)]">
          <span className="flex items-center gap-2">
            <span className="inline-block h-0.5 w-6 bg-[var(--accent)]" />
            포트폴리오 {last.portfolio.toFixed(3)}
          </span>
          <span className="flex items-center gap-2">
            <span className="inline-block h-0.5 w-6 border-t border-dashed border-[var(--muted)]" />
            벤치마크 {last.benchmark.toFixed(3)}
          </span>
        </div>
      </div>

      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="w-full max-w-full"
        role="img"
        aria-label="백테스트 자산 곡선"
      >
        {[0, 0.25, 0.5, 0.75, 1].map((t) => {
          const y = padding.top + innerH * (1 - t);
          const label = (minY + rangeY * t).toFixed(2);
          return (
            <g key={t}>
              <line
                x1={padding.left}
                y1={y}
                x2={width - padding.right}
                y2={y}
                stroke="var(--border)"
                strokeWidth="1"
              />
              <text x={4} y={y + 4} fill="var(--muted)" fontSize="10">
                {label}
              </text>
            </g>
          );
        })}

        <path
          d={toPath("benchmark")}
          fill="none"
          stroke="var(--muted)"
          strokeWidth="1.5"
          strokeDasharray="4 4"
        />
        <path
          d={toPath("portfolio")}
          fill="none"
          stroke="var(--accent)"
          strokeWidth="2"
        />

        {points.map((p, i) => (
          <text
            key={p.date}
            x={xAt(i)}
            y={height - 6}
            fill="var(--muted)"
            fontSize="9"
            textAnchor={i === 0 ? "start" : i === points.length - 1 ? "end" : "middle"}
          >
            {p.date.slice(5)}
          </text>
        ))}
      </svg>
    </div>
  );
}
