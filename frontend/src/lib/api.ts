import type { ScreenerResponse, StockDetailResponse } from "@/types/screener";
import type { BacktestQueryParams, BacktestResponse } from "@/types/backtest";
import {
  buildApiUrl,
  getApiConnectionHint,
  getApiBaseForDebug,
} from "@/lib/api-config";
import { ApiError, userMessageForStatus } from "@/lib/api-errors";
import {
  screenerDetailQueryString,
  screenerQueryString,
  type ScreenerQueryParams,
} from "@/lib/screener-query";
import { backtestQueryString } from "@/lib/backtest-query";

export { getApiBaseForDebug };
export { ApiError, getUserErrorMessage } from "@/lib/api-errors";

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const url = buildApiUrl(path);
  let res: Response;
  try {
    res = await fetch(url, {
      cache: "no-store",
      ...init,
      headers: {
        Accept: "application/json",
        ...init?.headers,
      },
    });
  } catch (cause) {
    throw new ApiError(
      0,
      "서버에 연결하지 못했습니다. 잠시 후 다시 시도해 주세요.",
      cause instanceof Error ? cause.message : getApiConnectionHint()
    );
  }

  if (!res.ok) {
    await res.text().catch(() => "");
    throw new ApiError(
      res.status,
      userMessageForStatus(res.status),
      `${res.status} ${url}`
    );
  }
  return res.json() as Promise<T>;
}

export function getScreener(params?: ScreenerQueryParams): Promise<ScreenerResponse> {
  return fetchJson<ScreenerResponse>(`/api/v1/screener${screenerQueryString(params)}`);
}

export function getStockDetail(
  ticker: string,
  market = "KOSPI"
): Promise<StockDetailResponse> {
  return fetchJson<StockDetailResponse>(
    `/api/v1/screener/${ticker}${screenerDetailQueryString(market)}`
  );
}

export function runBacktest(params?: BacktestQueryParams): Promise<BacktestResponse> {
  return fetchJson<BacktestResponse>(`/api/v1/backtest${backtestQueryString(params)}`);
}
