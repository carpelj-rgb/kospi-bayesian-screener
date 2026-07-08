/**
 * Browser always calls same-origin `/api/...`.
 * Next.js route handlers proxy to Render/local backend (CORS-free).
 *
 * Vercel: set BACKEND_URL=https://kospi-screener-api.onrender.com (server env)
 * Do NOT set NEXT_PUBLIC_API_URL unless you need direct browser → backend calls.
 */
export function buildApiUrl(path: string): string {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return normalizedPath;
}

export function getApiBaseForDebug(): string {
  return "(same-origin → Next.js proxy → backend)";
}

export function getApiConnectionHint(): string {
  return "Vercel/Render 백엔드(BACKEND_URL) 설정 및 Render 서비스 기동 상태를 확인하세요.";
}
