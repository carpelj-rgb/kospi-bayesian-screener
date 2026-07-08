import type { BacktestPeriodRow } from "@/types/backtest";
import { fmtSignedPct } from "@/lib/format";

interface BacktestPeriodsTableProps {
  periods: BacktestPeriodRow[];
}

export function BacktestPeriodsTable({ periods }: BacktestPeriodsTableProps) {
  if (!periods.length) {
    return null;
  }

  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)]/40 overflow-hidden">
      <div className="border-b border-[var(--border)] px-5 py-3">
        <h3 className="text-sm font-semibold">리밸런싱 구간</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="border-b border-[var(--border)] text-left text-[var(--muted)]">
              <th className="px-5 py-3 font-medium">시작</th>
              <th className="px-5 py-3 font-medium">종료</th>
              <th className="px-5 py-3 font-medium">보유 종목</th>
              <th className="px-5 py-3 font-medium text-right">수익률</th>
              <th className="px-5 py-3 font-medium text-right">벤치마크</th>
            </tr>
          </thead>
          <tbody>
            {periods.map((row) => (
              <tr key={`${row.rebalance_date}-${row.next_date}`} className="border-b border-[var(--border)]/60">
                <td className="px-5 py-3 tabular-nums">{row.rebalance_date}</td>
                <td className="px-5 py-3 tabular-nums">{row.next_date}</td>
                <td className="px-5 py-3 font-mono text-xs">
                  {row.holdings.join(", ")}
                </td>
                <td
                  className={`px-5 py-3 text-right tabular-nums ${
                    row.period_return >= 0 ? "text-[var(--positive)]" : "text-red-400"
                  }`}
                >
                  {fmtSignedPct(row.period_return)}
                </td>
                <td className="px-5 py-3 text-right tabular-nums text-[var(--muted)]">
                  {fmtSignedPct(row.benchmark_return)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
