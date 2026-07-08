import { NextRequest, NextResponse } from "next/server";
import { getBackendUrl, proxyToBackend } from "@/lib/backend-proxy";

export const maxDuration = 60;

export async function GET(request: NextRequest) {
  const path = `/api/v1/health${request.nextUrl.search}`;
  try {
    const res = await proxyToBackend(path);
    const body = await res.text();
    return new NextResponse(body, {
      status: res.status,
      headers: { "Content-Type": "application/json" },
    });
  } catch {
    return NextResponse.json(
      { detail: `백엔드(${getBackendUrl()})에 연결하지 못했습니다.` },
      { status: 502 }
    );
  }
}
