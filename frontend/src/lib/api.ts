import type { ScreenerResponse, StockDetailResponse } from "@/types/screener";
import {
  buildApiUrl,
  getApiConnectionHint,
  getApiBaseForDebug,
} from "@/lib/api-config";
import {
  screenerDetailQueryString,
  screenerQueryString,
  type ScreenerQueryParams,
} from "@/lib/screener-query";

export { getApiBaseForDebug };

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
  } catch {
    throw new Error(
      `네트워크 오류: ${url} 에 연결하지 못했습니다. ${getApiConnectionHint()}`
    );
  }

  if (!res.ok) {
    const body = await res.text().catch(() => "");
    const hint =
      res.status === 404
        ? " 백엔드(8000) 실행 여부 또는 Vercel BACKEND_URL(Render URL) 설정을 확인하세요."
        : "";
    throw new Error(
      `API error ${res.status} (${url})${body ? `: ${body.slice(0, 120)}` : ""}${hint}`
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
