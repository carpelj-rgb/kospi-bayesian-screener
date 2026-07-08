const TAG_META: Record<string, { label: string; className: string }> = {
  Revision: {
    label: "EPS 상향",
    className: "border-sky-700/50 bg-sky-950/50 text-sky-300",
  },
  "ROE↑": {
    label: "저PBR+ROE",
    className: "border-violet-700/50 bg-violet-950/50 text-violet-300",
  },
  수급전환: {
    label: "수급 턴어라운드",
    className: "border-amber-700/50 bg-amber-950/50 text-amber-300",
  },
  VCP: {
    label: "VCP 돌파",
    className: "border-orange-700/50 bg-orange-950/50 text-orange-300",
  },
  내부자매수: {
    label: "내부자 매수",
    className: "border-pink-700/50 bg-pink-950/50 text-pink-300",
  },
  재무안정: {
    label: "재무 안정",
    className: "border-teal-700/50 bg-teal-950/50 text-teal-300",
  },
};

function resolveTags(tags: string[]): { key: string; label: string; className: string }[] {
  return tags.map((tag) => {
    const meta = TAG_META[tag];
    return {
      key: tag,
      label: meta?.label ?? tag,
      className: meta?.className ?? "border-emerald-700/50 bg-emerald-950/50 text-emerald-300",
    };
  });
}

export function FactorTags({ tags }: { tags: string[] }) {
  const resolved = resolveTags(tags);

  if (resolved.length === 0) {
    return (
      <span className="text-xs text-[var(--muted)]">충족 팩터 없음</span>
    );
  }

  return (
    <div className="flex flex-wrap gap-1.5 max-w-[280px]">
      {resolved.map(({ key, label, className }) => (
        <span
          key={key}
          title={key}
          className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${className}`}
        >
          {label}
        </span>
      ))}
    </div>
  );
}
