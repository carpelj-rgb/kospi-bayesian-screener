"use client";

import { useCallback, useMemo, useState } from "react";
import type { ScreenerResponse, ScreenerRow } from "@/types/screener";
import { getScreener, getStockDetail } from "@/lib/api";
import { ScreenerTable } from "./ScreenerTable";

function sortByPosterior(rows: ScreenerRow[]): ScreenerRow[] {
  return [...rows].sort(
    (a, b) => b.posterior_up_prob - a.posterior_up_prob
  );
}

function matchesQuery(row: ScreenerRow, query: string): boolean {
  const q = query.trim().toLowerCase();
  if (!q) return true;
  return (
    row.ticker.includes(q) ||
    row.name.toLowerCase().includes(q)
  );
}

export function ScreenerDashboard() {
  const [query, setQuery] = useState("");
  const [market, setMarket] = useState("KOSPI");
  const [limit, setLimit] = useState(20);
  const [rows, setRows] = useState<ScreenerRow[]>([]);
  const [meta, setMeta] = useState<Pick<ScreenerResponse, "market" | "as_of" | "count"> | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [warnings, setWarnings] = useState<string[]>([]);
  const [hasScreened, setHasScreened] = useState(false);

  const runScreening = useCallback(async () => {
    setLoading(true);
    setError(null);
    setWarnings([]);
    try {
      const data = await getScreener({ market, limit });
      setRows(sortByPosterior(data.rows));
      setMeta({ market: data.market, as_of: data.as_of, count: data.count });
      setWarnings(data.warnings ?? []);
      setHasScreened(true);
    } catch (e) {
      setError(
        e instanceof Error
          ? e.message
          : "스크리닝 데이터를 불러오지 못했습니다."
      );
    } finally {
      setLoading(false);
    }
  }, [market, limit]);

  const searchTicker = useCallback(async () => {
    const trimmed = query.trim();
    setError(null);

    if (!trimmed) {
      if (!hasScreened) {
        await runScreening();
      }
      return;
    }

    setLoading(true);
    try {
      const isTicker = /^\d{6}$/.test(trimmed);

      if (isTicker) {
        const detail = await getStockDetail(trimmed, market);
        setRows([detail.row]);
        setMeta({
          market: detail.row.market,
          as_of: detail.row.as_of,
          count: 1,
        });
        setHasScreened(true);
        return;
      }

      if (!hasScreened) {
        const data = await getScreener({ market, limit });
        setRows(sortByPosterior(data.rows));
        setMeta({ market: data.market, as_of: data.as_of, count: data.count });
        setWarnings(data.warnings ?? []);
        setHasScreened(true);
      }
    } catch (e) {
      setError(
        e instanceof Error ? e.message : "종목 검색에 실패했습니다."
      );
    } finally {
      setLoading(false);
    }
  }, [query, market, limit, hasScreened, runScreening]);

  const displayedRows = useMemo(() => {
    if (!query.trim()) {
      return sortByPosterior(rows);
    }
    return sortByPosterior(rows.filter((r) => matchesQuery(r, query)));
  }, [rows, query]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    searchTicker();
  };

  return (
    <div className="space-y-6">
      <section className="rounded-xl border border-[var(--border)] bg-[var(--surface)]/40 p-5">
        <form onSubmit={handleSubmit} className="flex flex-col gap-4 lg:flex-row lg:items-end">
          <div className="flex-1">
            <label
              htmlFor="ticker-search"
              className="mb-1.5 block text-xs font-medium text-[var(--muted)]"
            >
              종목 검색 (티커 또는 종목명)
            </label>
            <input
              id="ticker-search"
              type="search"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="예: 005930, 삼성전자"
              className="w-full rounded-lg border border-[var(--border)] bg-[var(--bg)] px-4 py-2.5 text-sm outline-none ring-[var(--accent)] placeholder:text-[var(--muted)] focus:ring-2"
            />
          </div>

          <div className="flex flex-wrap gap-3">
            <div>
              <label
                htmlFor="market-select"
                className="mb-1.5 block text-xs font-medium text-[var(--muted)]"
              >
                시장
              </label>
              <select
                id="market-select"
                value={market}
                onChange={(e) => setMarket(e.target.value)}
                className="rounded-lg border border-[var(--border)] bg-[var(--bg)] px-3 py-2.5 text-sm outline-none focus:ring-2 focus:ring-[var(--accent)]"
              >
                <option value="KOSPI">KOSPI</option>
                <option value="KOSDAQ">KOSDAQ</option>
              </select>
            </div>

            <div>
              <label
                htmlFor="limit-select"
                className="mb-1.5 block text-xs font-medium text-[var(--muted)]"
              >
                유니버스
              </label>
              <select
                id="limit-select"
                value={limit}
                onChange={(e) => setLimit(Number(e.target.value))}
                className="rounded-lg border border-[var(--border)] bg-[var(--bg)] px-3 py-2.5 text-sm outline-none focus:ring-2 focus:ring-[var(--accent)]"
              >
                <option value={20}>20종목</option>
                <option value={30}>30종목</option>
                <option value={50}>50종목</option>
              </select>
            </div>
          </div>

          <div className="flex gap-2">
            <button
              type="submit"
              disabled={loading}
              className="rounded-lg border border-[var(--border)] bg-[var(--bg)] px-4 py-2.5 text-sm font-medium transition hover:bg-[var(--surface)] disabled:opacity-50"
            >
              검색
            </button>
            <button
              type="button"
              onClick={runScreening}
              disabled={loading}
              className="rounded-lg bg-[var(--accent)] px-5 py-2.5 text-sm font-semibold text-white transition hover:brightness-110 disabled:opacity-50"
            >
              {loading ? "계산 중…" : "스크리닝 실행"}
            </button>
          </div>
        </form>

        {meta && hasScreened && (
          <p className="mt-4 text-xs text-[var(--muted)]">
            {meta.market} · 기준일 {meta.as_of} · {displayedRows.length}종목
            {query.trim() ? " (필터 적용)" : ""}
          </p>
        )}
      </section>

      {warnings.length > 0 && (
        <div className="rounded-lg border border-amber-800/80 bg-amber-950/20 px-5 py-4">
          <p className="font-medium text-amber-300">데이터 경고</p>
          <ul className="mt-1 list-disc pl-5 text-sm text-[var(--muted)]">
            {warnings.map((w) => (
              <li key={w}>{w}</li>
            ))}
          </ul>
        </div>
      )}

      {error && (
        <div className="rounded-lg border border-red-800/80 bg-red-950/30 px-5 py-4">
          <p className="font-medium text-red-300">오류</p>
          <p className="mt-1 text-sm text-[var(--muted)]">{error}</p>
          <p className="mt-2 text-xs text-[var(--muted)]">
            백엔드 실행:{" "}
            <code className="rounded bg-[var(--surface)] px-1 py-0.5">
              uvicorn app.main:app --reload
            </code>
          </p>
        </div>
      )}

      {!hasScreened && !loading && !error && (
        <div className="rounded-xl border border-dashed border-[var(--border)] py-20 text-center">
          <p className="text-lg font-medium">스크리닝을 시작하세요</p>
          <p className="mt-2 text-sm text-[var(--muted)]">
            「스크리닝 실행」을 누르면 π(상승 확률) 높은 순으로 정렬됩니다.
            (첫 실행은 30~60초 걸릴 수 있습니다)
          </p>
        </div>
      )}

      {(hasScreened || loading) && (
        <>
          {loading && (
            <p className="text-center text-sm text-[var(--muted)] py-4">
              API에서 데이터를 불러오는 중…
            </p>
          )}
          <ScreenerTable
            rows={
              loading && rows.length === 0
                ? []
                : displayedRows
            }
          />
          {!loading && hasScreened && displayedRows.length === 0 && rows.length > 0 && (
            <p className="mt-2 text-center text-sm text-amber-400/90">
              검색어와 일치하는 종목이 없습니다. 검색어를 지우거나 변경해 보세요.
            </p>
          )}
        </>
      )}
    </div>
  );
}
