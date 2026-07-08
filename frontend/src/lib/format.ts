export function fmtPct(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

export function fmtPrice(value: number | null): string {
  if (value == null) return "—";
  return `${value.toLocaleString("ko-KR", { maximumFractionDigits: 0 })}원`;
}
