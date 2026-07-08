import { fmtPct } from "@/lib/format";

function barColor(pct: number): string {
  if (pct >= 70) return "from-emerald-400 to-green-500";
  if (pct >= 60) return "from-emerald-500 to-teal-400";
  if (pct >= 55) return "from-blue-500 to-cyan-400";
  if (pct >= 50) return "from-slate-400 to-slate-500";
  return "from-slate-600 to-slate-700";
}

function textColor(pct: number): string {
  if (pct >= 60) return "text-emerald-300";
  if (pct >= 55) return "text-blue-300";
  return "text-[var(--text)]";
}

export function PosteriorBar({
  prob,
  probPct,
}: {
  prob: number;
  probPct?: number;
}) {
  const pct = Math.min(100, Math.max(0, probPct ?? prob * 100));
  const display = probPct != null ? `${probPct.toFixed(1)}%` : fmtPct(prob);

  return (
    <div className="min-w-[200px]">
      <div className="mb-2 flex items-end justify-between gap-3">
        <span className="text-[11px] font-medium uppercase tracking-wide text-[var(--muted)]">
          Posterior π
        </span>
        <span className={`text-lg font-bold tabular-nums leading-none ${textColor(pct)}`}>
          {display}
        </span>
      </div>
      <div className="relative h-3 w-full overflow-hidden rounded-full bg-[var(--border)]/80">
        <div
          className={`absolute inset-y-0 left-0 rounded-full bg-gradient-to-r transition-all duration-700 ease-out ${barColor(pct)}`}
          style={{ width: `${pct}%` }}
          role="progressbar"
          aria-valuenow={Math.round(pct * 10) / 10}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label={`상승 확률 ${display}`}
        />
      </div>
      <div className="mt-1 flex justify-between text-[10px] text-[var(--muted)]">
        <span>0%</span>
        <span>100%</span>
      </div>
    </div>
  );
}
