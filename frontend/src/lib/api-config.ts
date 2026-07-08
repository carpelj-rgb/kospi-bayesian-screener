/**
 * API base URL resolution for local dev vs cloud deployment.
 *
 * Local dev (default): leave NEXT_PUBLIC_API_URL unset → same-origin `/api/...`
 *   (Next.js rewrite or route handler → backend)
 *
 * Vercel / production: set NEXT_PUBLIC_API_URL to the public backend URL, e.g.
 *   https://kospi-screener-api.onrender.com
 */
const RAW_API_BASE = process.env.NEXT_PUBLIC_API_URL?.trim() ?? "";

export function getPublicApiBaseUrl(): string {
  return RAW_API_BASE.replace(/\/$/, "");
}

export function isDirectApiMode(): boolean {
  return getPublicApiBaseUrl().length > 0;
}

export function buildApiUrl(path: string): string {
  const base = getPublicApiBaseUrl();
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return base ? `${base}${normalizedPath}` : normalizedPath;
}

export function getApiBaseForDebug(): string {
  if (isDirectApiMode()) {
    return getPublicApiBaseUrl();
  }
  return "(same-origin proxy → backend)";
}

export function getApiConnectionHint(): string {
  if (isDirectApiMode()) {
    return `API 주소(${getPublicApiBaseUrl()})와 백엔드 CORS 설정을 확인하세요.`;
  }
  return "백엔드(8000) 실행 및 Next.js dev 서버 재시작을 확인하세요.";
}
