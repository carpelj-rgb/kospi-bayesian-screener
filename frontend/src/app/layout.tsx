import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "KOSPI Bayesian Factor Screener",
  description: "PBR, 수급 턴어라운드, EPS 상향 팩터 기반 베이지안 스크리너",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  );
}
