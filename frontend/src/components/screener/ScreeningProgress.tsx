"use client";

type ScreeningProgressProps = {
  currentStep: string;
  stepIndex: number;
  steps: { label: string }[];
};

export function ScreeningProgress({
  currentStep,
  stepIndex,
  steps,
}: ScreeningProgressProps) {
  const progressPct = Math.round(((stepIndex + 1) / steps.length) * 100);

  return (
    <div
      className="rounded-xl border border-[var(--border)] bg-[var(--surface)]/60 px-5 py-6"
      role="status"
      aria-live="polite"
      aria-busy="true"
    >
      <div className="flex items-start gap-4">
        <div
          className="mt-0.5 h-6 w-6 shrink-0 animate-spin rounded-full border-2 border-[var(--accent)] border-t-transparent"
          aria-hidden="true"
        />
        <div className="min-w-0 flex-1 space-y-3">
          <div>
            <p className="text-sm font-medium text-[var(--foreground)]">
              스크리닝 진행 중
            </p>
            <p className="mt-1 text-sm text-[var(--muted)]">{currentStep}</p>
          </div>

          <div className="h-1.5 overflow-hidden rounded-full bg-[var(--border)]">
            <div
              className="h-full rounded-full bg-[var(--accent)] transition-all duration-700 ease-out"
              style={{ width: `${progressPct}%` }}
            />
          </div>

          <ol className="space-y-1.5 text-xs text-[var(--muted)]">
            {steps.map((step, index) => {
              const done = index < stepIndex;
              const current = index === stepIndex;
              return (
                <li
                  key={step.label}
                  className={
                    current
                      ? "font-medium text-[var(--accent)]"
                      : done
                        ? "text-[var(--foreground)]/70"
                        : ""
                  }
                >
                  {done ? "✓ " : current ? "→ " : "· "}
                  {step.label}
                </li>
              );
            })}
          </ol>

          <p className="text-xs text-[var(--muted)]">
            첫 실행은 30~60초 걸릴 수 있습니다. Render cold start 시 1~2분
            더 소요될 수 있습니다.
          </p>
        </div>
      </div>
    </div>
  );
}
