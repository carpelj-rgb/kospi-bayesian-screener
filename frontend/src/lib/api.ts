import type { ScreenerResponse, StockDetailResponse } from "@/types/screener";
import {
  buildApiUrl,
  getApiConnectionHint,
  getApiBaseForDebug,
} from "@/lib/api-config";

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

export function getScreener(params?: {
  market?: string;
  min_prob?: number;
  limit?: number;
}): Promise<ScreenerResponse> {
  const search = new URLSearchParams();
  if (params?.market) search.set("market", params.market);
  if (params?.min_prob != null) search.set("min_prob", String(params.min_prob));
  if (params?.limit != null) search.set("limit", String(params.limit));
  const qs = search.toString();
  return fetchJson<ScreenerResponse>(`/api/v1/screener${qs ? `?${qs}` : ""}`);
}

export function getStockDetail(
  ticker: string,
  market = "KOSPI"
): Promise<StockDetailResponse> {
  return fetchJson<StockDetailResponse>(
    `/api/v1/screener/${ticker}?market=${market}`
  );
}
