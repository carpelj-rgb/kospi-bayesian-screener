import type { BacktestMetrics } from "@/types/backtest";
import { fmtPct, fmtSignedPct } from "@/lib/format";

interface BacktestMetricsCardsProps {
  metrics: BacktestMetrics;
}

function MetricCard({
  label,
  value,
  tone = "default",
}: {
  label: string;
  value: string;
  tone?: "default" | "positive" | "negative";
}) {
  const color =
    tone === "positive"
      ? "text-[var(--positive)]"
      : tone === "negative"
        ? "text-red-400"
        : "text-[var(--text)]";

  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)]/40 p-4">
      <p className="text-xs uppercase tracking-wide text-[var(--muted)]">{label}</p>
      <p className={`mt-2 text-2xl font-semibold tabular-nums ${color}`}>{value}</p>
    </div>
  );
}

export function BacktestMetricsCards({ metrics }: BacktestMetricsCardsProps) {
  const returnTone = metrics.total_return >= 0 ? "positive" : "negative";
  const benchTone = metrics.benchmark_total_return >= 0 ? "positive" : "negative";

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
      <MetricCard label="누적 수익률" value={fmtSignedPct(metrics.total_return)} tone={returnTone} />
      <MetricCard
        label="벤치마크 수익률"
        value={fmtSignedPct(metrics.benchmark_total_return)}
        tone={benchTone}
      />
      <MetricCard label="MDD" value={fmtPct(metrics.max_drawdown)} tone="negative" />
      <MetricCard
        label="샤프 지수"
        value={metrics.sharpe_ratio != null ? metrics.sharpe_ratio.toFixed(2) : "—"}
      />
      <MetricCard label="리밸런싱 횟수" value={String(metrics.periods)} />
      <MetricCard label="승률" value={fmtPct(metrics.win_rate)} />
    </div>
  );
}
