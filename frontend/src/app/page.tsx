import { ScreenerDashboard } from "@/components/screener/ScreenerDashboard";

export default function HomePage() {
  return (
    <main className="min-h-screen p-6 md:p-10 max-w-7xl mx-auto">
      <header className="mb-8">
        <h1 className="text-2xl md:text-3xl font-bold tracking-tight">
          KOSPI Bayesian Factor Screener
        </h1>
        <p className="mt-2 text-[var(--muted)]">
          팩터 배지 + Posterior π 프로그레스 바 · 컬럼 클릭 정렬 지원
        </p>
      </header>

      <ScreenerDashboard />
    </main>
  );
}
