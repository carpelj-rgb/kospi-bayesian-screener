import { NextRequest, NextResponse } from "next/server";
import { getBackendUrl, proxyToBackend } from "@/lib/backend-proxy";

export const maxDuration = 60;

export async function GET(request: NextRequest) {
  const path = `/api/v1/screener${request.nextUrl.search}`;
  try {
    const res = await proxyToBackend(path);
    const body = await res.text();
    if (res.status === 404) {
      return NextResponse.json(
        {
          detail: `백엔드(${getBackendUrl()})에서 404 — FastAPI가 실행 중인지, 경로 ${path} 가 존재하는지 확인하세요.`,
        },
        { status: 502 }
      );
    }
    return new NextResponse(body, {
      status: res.status,
      headers: { "Content-Type": "application/json" },
    });
  } catch {
    return NextResponse.json(
      {
        detail: `백엔드(${getBackendUrl()})에 연결하지 못했습니다. Render 서비스가 실행 중인지 확인하세요.`,
      },
      { status: 502 }
    );
  }
}
