/** Query params accepted by GET /api/v1/screener (backend/app/api/v1/screener.py). */
export const SCREENER_MARKETS = ["KOSPI", "KOSDAQ"] as const;
export type ScreenerMarket = (typeof SCREENER_MARKETS)[number];

export type ScreenerQueryParams = {
  market?: string;
  min_prob?: number;
  limit?: number;
};

const DEFAULT_MARKET: ScreenerMarket = "KOSPI";
const MIN_LIMIT = 1;
const MAX_LIMIT = 200;

function normalizeMarket(value: string | null | undefined): ScreenerMarket {
  const upper = value?.trim().toUpperCase();
  if (upper && SCREENER_MARKETS.includes(upper as ScreenerMarket)) {
    return upper as ScreenerMarket;
  }
  return DEFAULT_MARKET;
}

function normalizeLimit(value: number | null | undefined): number | undefined {
  if (value == null || !Number.isFinite(value)) {
    return undefined;
  }
  return Math.min(MAX_LIMIT, Math.max(MIN_LIMIT, Math.round(value)));
}

function normalizeMinProb(value: number | null | undefined): number | undefined {
  if (value == null || !Number.isFinite(value)) {
    return undefined;
  }
  return Math.min(1, Math.max(0, value));
}

/** Build validated query string for the screener list endpoint. */
export function buildScreenerSearchParams(
  params?: ScreenerQueryParams
): URLSearchParams {
  const search = new URLSearchParams();
  search.set("market", normalizeMarket(params?.market));

  const limit = normalizeLimit(params?.limit);
  if (limit != null) {
    search.set("limit", String(limit));
  }

  const minProb = normalizeMinProb(params?.min_prob);
  if (minProb != null) {
    search.set("min_prob", String(minProb));
  }

  return search;
}

export function screenerQueryString(params?: ScreenerQueryParams): string {
  const qs = buildScreenerSearchParams(params).toString();
  return qs ? `?${qs}` : "";
}

/** Detail endpoint only accepts `market`. */
export function screenerDetailQueryString(market?: string): string {
  const search = new URLSearchParams();
  search.set("market", normalizeMarket(market));
  return `?${search.toString()}`;
}

/** Sanitize inbound proxy query params before forwarding to FastAPI. */
export function sanitizeScreenerSearchParams(
  source: URLSearchParams
): URLSearchParams {
  const limitRaw = source.get("limit");
  const minProbRaw = source.get("min_prob");

  let limit: number | undefined;
  if (limitRaw != null && limitRaw !== "") {
    const parsed = Number.parseInt(limitRaw, 10);
    limit = Number.isNaN(parsed) ? undefined : parsed;
  }

  let minProb: number | undefined;
  if (minProbRaw != null && minProbRaw !== "") {
    const parsed = Number.parseFloat(minProbRaw);
    minProb = Number.isNaN(parsed) ? undefined : parsed;
  }

  return buildScreenerSearchParams({
    market: source.get("market") ?? undefined,
    limit,
    min_prob: minProb,
  });
}
