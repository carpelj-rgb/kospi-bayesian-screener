import { useEffect, useMemo, useState } from "react";

export type ScreeningStep = {
  label: string;
  durationMs: number;
};

export function buildScreeningSteps(market: string, limit: number): ScreeningStep[] {
  return [
    { label: `${market} 유니버스 로딩 중… (${limit}종목)`, durationMs: 8_000 },
    {
      label: "팩터 데이터 수집 중… (Revision · 수급 · VCP · 재무)",
      durationMs: 18_000,
    },
    { label: "베이지안 팩터 계산 중…", durationMs: 15_000 },
    { label: "π(상승 확률) 순위 정렬 중…", durationMs: 20_000 },
  ];
}

export function useScreeningProgress(
  active: boolean,
  market: string,
  limit: number
) {
  const steps = useMemo(
    () => buildScreeningSteps(market, limit),
    [market, limit]
  );
  const [stepIndex, setStepIndex] = useState(0);

  useEffect(() => {
    if (!active) {
      setStepIndex(0);
      return;
    }

    setStepIndex(0);
    let elapsed = 0;
    const timers: ReturnType<typeof setTimeout>[] = [];

    for (let i = 0; i < steps.length - 1; i += 1) {
      elapsed += steps[i].durationMs;
      timers.push(
        setTimeout(() => {
          setStepIndex(i + 1);
        }, elapsed)
      );
    }

    return () => {
      timers.forEach(clearTimeout);
    };
  }, [active, steps]);

  const currentStep = steps[Math.min(stepIndex, steps.length - 1)]?.label ?? "";

  return {
    steps,
    stepIndex: Math.min(stepIndex, steps.length - 1),
    currentStep,
    totalSteps: steps.length,
  };
}
