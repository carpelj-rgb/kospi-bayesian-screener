"use client";

import { useCallback, useState } from "react";
import type { BacktestResponse } from "@/types/backtest";
import { getUserErrorMessage, runBacktest } from "@/lib/api";
import { BacktestEquityChart } from "./BacktestEquityChart";
import { BacktestMetricsCards } from "./BacktestMetricsCards";
import { BacktestPeriodsTable } from "./BacktestPeriodsTable";

export function BacktestDashboard() {
  const [market, setMarket] = useState("KOSPI");
  const [topN, setTopN] = useState(10);
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<BacktestResponse | null>(null);

  const handleRun = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await runBacktest({
        market,
        top_n: topN,
        start_date: startDate || undefined,
        end_date: endDate || undefined,
      });
      setResult(data);
    } catch (e) {
      setError(getUserErrorMessage(e));
      setResult(null);
    } finally {
      setLoading(false);
    }
  }, [market, topN, startDate, endDate]);

  return (
    <div className="space-y-6">
      <section className="rounded-xl border border-[var(--border)] bg-[var(--surface)]/40 p-5">
        <p className="text-sm text-[var(--muted)] mb-4">
          SQLite에 저장된 일별 팩터 스냅샷을 사용해 베이지안 π 상위 종목의
          동일가중 리밸런싱 성과를 계산합니다. 스냅샷이 2일 이상 쌓여 있어야 합니다.
        </p>

        <div className="flex flex-wrap items-end gap-4">
          <label className="flex flex-col gap-1.5 text-sm">
            <span className="text-[var(--muted)]">시장</span>
            <select
              value={market}
              onChange={(e) => setMarket(e.target.value)}
              disabled={loading}
              className="rounded-lg border border-[var(--border)] bg-[var(--bg)] px-3 py-2 focus:outline-none focus:ring-2 focus:ring-[var(--accent)]"
            >
              <option value="KOSPI">KOSPI</option>
              <option value="KOSDAQ">KOSDAQ</option>
            </select>
          </label>

          <label className="flex flex-col gap-1.5 text-sm">
            <span className="text-[var(--muted)]">상위 N 종목</span>
            <input
              type="number"
              min={1}
              max={50}
              value={topN}
              onChange={(e) => setTopN(Number(e.target.value) || 10)}
              disabled={loading}
              className="w-24 rounded-lg border border-[var(--border)] bg-[var(--bg)] px-3 py-2 tabular-nums focus:outline-none focus:ring-2 focus:ring-[var(--accent)]"
            />
          </label>

          <label className="flex flex-col gap-1.5 text-sm">
            <span className="text-[var(--muted)]">시작일 (선택)</span>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              disabled={loading}
              className="rounded-lg border border-[var(--border)] bg-[var(--bg)] px-3 py-2 focus:outline-none focus:ring-2 focus:ring-[var(--accent)]"
            />
          </label>

          <label className="flex flex-col gap-1.5 text-sm">
            <span className="text-[var(--muted)]">종료일 (선택)</span>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              disabled={loading}
              className="rounded-lg border border-[var(--border)] bg-[var(--bg)] px-3 py-2 focus:outline-none focus:ring-2 focus:ring-[var(--accent)]"
            />
          </label>

          <button
            type="button"
            onClick={handleRun}
            disabled={loading}
            className="rounded-lg bg-[var(--accent)] px-5 py-2.5 text-sm font-medium text-white hover:brightness-110 disabled:opacity-50"
          >
            {loading ? "계산 중…" : "백테스트 실행"}
          </button>
        </div>
      </section>

      {error && (
        <div className="rounded-xl border border-red-500/40 bg-red-500/10 px-5 py-4 text-sm text-red-300">
          {error}
        </div>
      )}

      {result && (
        <>
          {result.warnings.length > 0 && (
            <div className="rounded-xl border border-amber-500/40 bg-amber-500/10 px-5 py-4 text-sm text-amber-200">
              <ul className="list-disc pl-5 space-y-1">
                {result.warnings.map((w) => (
                  <li key={w}>{w}</li>
                ))}
              </ul>
            </div>
          )}

          <BacktestMetricsCards metrics={result.metrics} />
          <BacktestEquityChart points={result.equity_curve} />
          <BacktestPeriodsTable periods={result.periods} />

          {result.snapshot_dates_used.length > 0 && (
            <p className="text-xs text-[var(--muted)]">
              사용된 스냅샷 날짜: {result.snapshot_dates_used.join(", ")}
            </p>
          )}
        </>
      )}

      {!result && !error && !loading && (
        <div className="rounded-xl border border-dashed border-[var(--border)] bg-[var(--surface)]/20 px-5 py-10 text-center text-sm text-[var(--muted)]">
          백테스트 실행 버튼을 눌러 결과를 확인하세요.
        </div>
      )}
    </div>
  );
}
