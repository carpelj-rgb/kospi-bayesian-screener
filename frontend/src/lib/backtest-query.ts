import type { BacktestQueryParams } from "@/types/backtest";

export const BACKTEST_MARKETS = ["KOSPI", "KOSDAQ"] as const;

function normalizeOptionalString(value: string | null | undefined): string | undefined {
  const trimmed = value?.trim();
  return trimmed ? trimmed : undefined;
}

function normalizeOptionalInt(value: string | null | undefined): number | undefined {
  const text = normalizeOptionalString(value);
  if (!text) return undefined;
  const parsed = Number.parseInt(text, 10);
  return Number.isFinite(parsed) ? parsed : undefined;
}

export function buildBacktestSearchParams(params?: BacktestQueryParams): URLSearchParams {
  const sp = new URLSearchParams();
  if (!params) return sp;

  if (params.market) sp.set("market", params.market);
  if (params.top_n != null) sp.set("top_n", String(params.top_n));
  if (params.start_date) sp.set("start_date", params.start_date);
  if (params.end_date) sp.set("end_date", params.end_date);
  return sp;
}

export function sanitizeBacktestSearchParams(source: URLSearchParams): URLSearchParams {
  const market = normalizeOptionalString(source.get("market")) ?? "KOSPI";
  const topN = normalizeOptionalInt(source.get("top_n")) ?? 10;
  const startDate = normalizeOptionalString(source.get("start_date"));
  const endDate = normalizeOptionalString(source.get("end_date"));

  const sp = new URLSearchParams();
  sp.set("market", market);
  sp.set("top_n", String(Math.min(50, Math.max(1, topN))));
  if (startDate) sp.set("start_date", startDate);
  if (endDate) sp.set("end_date", endDate);
  return sp;
}

export function backtestQueryString(params?: BacktestQueryParams): string {
  const qs = buildBacktestSearchParams(params).toString();
  return qs ? `?${qs}` : "";
}
