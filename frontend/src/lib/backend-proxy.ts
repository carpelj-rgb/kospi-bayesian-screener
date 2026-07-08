/** Shared server-side proxy target for Next.js API routes. */
export function getBackendUrl(): string {
  const url =
    process.env.BACKEND_URL ??
    process.env.NEXT_PUBLIC_API_URL ??
    "http://127.0.0.1:8000";
  return url.replace(/\/$/, "");
}

export const PROXY_TIMEOUT_MS = 120_000;

export async function proxyToBackend(
  pathWithQuery: string,
  init?: RequestInit
): Promise<Response> {
  const target = `${getBackendUrl()}${pathWithQuery.startsWith("/") ? pathWithQuery : `/${pathWithQuery}`}`;
  return fetch(target, {
    cache: "no-store",
    ...init,
    signal: init?.signal ?? AbortSignal.timeout(PROXY_TIMEOUT_MS),
    headers: {
      Accept: "application/json",
      ...init?.headers,
    },
  });
}
