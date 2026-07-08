"use client";

import { useState } from "react";
import { ScreenerDashboard } from "@/components/screener/ScreenerDashboard";
import { BacktestDashboard } from "@/components/backtest/BacktestDashboard";

export type AppTab = "screener" | "backtest";

const TABS: { id: AppTab; label: string; description: string }[] = [
  { id: "screener", label: "스크리너", description: "실시간 팩터 스크리닝" },
  { id: "backtest", label: "백테스트", description: "스냅샷 기반 성과 검증" },
];

export function AppShell() {
  const [tab, setTab] = useState<AppTab>("screener");

  return (
    <>
      <header className="mb-8">
        <h1 className="text-2xl md:text-3xl font-bold tracking-tight">
          KOSPI Bayesian Factor Screener
        </h1>
        <p className="mt-2 text-[var(--muted)]">
          {tab === "screener"
            ? "팩터 배지 + Posterior π 프로그레스 바 · 컬럼 클릭 정렬 지원"
            : "SQLite 스냅샷 기반 리밸런싱 수익률 · MDD · 샤프 지수"}
        </p>

        <nav
          className="mt-6 flex gap-1 border-b border-[var(--border)]"
          aria-label="주요 기능"
        >
          {TABS.map((item) => {
            const active = tab === item.id;
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => setTab(item.id)}
                className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
                  active
                    ? "border-[var(--accent)] text-[var(--text)]"
                    : "border-transparent text-[var(--muted)] hover:text-[var(--text)]"
                }`}
                aria-current={active ? "page" : undefined}
              >
                {item.label}
              </button>
            );
          })}
        </nav>
      </header>

      {tab === "screener" ? <ScreenerDashboard /> : <BacktestDashboard />}
    </>
  );
}
