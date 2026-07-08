import { NextRequest, NextResponse } from "next/server";

const BACKEND = process.env.BACKEND_URL ?? "http://127.0.0.1:8000";

export async function GET(
  request: NextRequest,
  { params }: { params: { ticker: string } }
) {
  const target = `${BACKEND}/api/v1/screener/${params.ticker}${request.nextUrl.search}`;
  try {
    const res = await fetch(target, { cache: "no-store" });
    const body = await res.text();
    return new NextResponse(body, {
      status: res.status,
      headers: { "Content-Type": "application/json" },
    });
  } catch {
    return NextResponse.json(
      { detail: `백엔드(${BACKEND})에 연결하지 못했습니다.` },
      { status: 502 }
    );
  }
}
