"use client";

import { useMemo, useState } from "react";
import type { ScreenerRow } from "@/types/screener";
import { fmtPrice } from "@/lib/format";
import { FactorTags } from "./FactorBadge";
import { PosteriorBar } from "./PosteriorBar";

type SortKey = "prob" | "name" | "price" | "factors";
type SortDir = "asc" | "desc";

function SortIcon({ active, dir }: { active: boolean; dir: SortDir }) {
  return (
    <span className={`ml-1 inline-block text-[10px] ${active ? "text-[var(--accent)]" : "text-[var(--muted)]/50"}`}>
      {active ? (dir === "asc" ? "▲" : "▼") : "↕"}
    </span>
  );
}

function SortableHeader({
  label,
  sortKey,
  activeKey,
  dir,
  onSort,
  align = "left",
}: {
  label: string;
  sortKey: SortKey;
  activeKey: SortKey;
  dir: SortDir;
  onSort: (key: SortKey) => void;
  align?: "left" | "right";
}) {
  const active = activeKey === sortKey;
  return (
    <th
      className={`px-5 py-3.5 font-medium ${align === "right" ? "text-right" : "text-left"}`}
    >
      <button
        type="button"
        onClick={() => onSort(sortKey)}
        className={`inline-flex items-center uppercase tracking-wide transition hover:text-[var(--text)] ${
          active ? "text-[var(--text)]" : "text-[var(--muted)]"
        } ${align === "right" ? "ml-auto" : ""}`}
      >
        {label}
        <SortIcon active={active} dir={dir} />
      </button>
    </th>
  );
}

function sortRows(rows: ScreenerRow[], key: SortKey, dir: SortDir): ScreenerRow[] {
  const mul = dir === "asc" ? 1 : -1;
  return [...rows].sort((a, b) => {
    switch (key) {
      case "prob":
        return mul * (a.posterior_up_prob - b.posterior_up_prob);
      case "name":
        return mul * a.name.localeCompare(b.name, "ko");
      case "price":
        return mul * ((a.price ?? 0) - (b.price ?? 0));
      case "factors":
        return mul * (a.factor_tags.length - b.factor_tags.length);
      default:
        return 0;
    }
  });
}

export function ScreenerTable({ rows }: { rows: ScreenerRow[] }) {
  const [sortKey, setSortKey] = useState<SortKey>("prob");
  const [sortDir, setSortDir] = useState<SortDir>("desc");

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir(key === "name" ? "asc" : "desc");
    }
  };

  const sortedRows = useMemo(
    () => sortRows(rows, sortKey, sortDir),
    [rows, sortKey, sortDir]
  );

  if (rows.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-[var(--border)] py-16 text-center">
        <p className="text-[var(--muted)]">표시할 종목이 없습니다.</p>
        <p className="mt-1 text-sm text-[var(--muted)]">
          스크리닝을 실행하거나 검색어를 변경해 보세요.
        </p>
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-xl border border-[var(--border)]">
      <div className="flex items-center justify-between border-b border-[var(--border)] bg-[var(--surface)]/60 px-5 py-2.5">
        <p className="text-xs text-[var(--muted)]">
          컬럼 헤더를 클릭해 정렬 · 기본: 상승 확률 높은 순
        </p>
        <p className="text-xs font-medium text-[var(--muted)]">
          {sortedRows.length}종목
        </p>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[860px] text-sm">
          <thead>
            <tr className="border-b border-[var(--border)] bg-[var(--surface)] text-xs">
              <th className="w-14 px-5 py-3.5 text-left font-medium text-[var(--muted)]">
                #
              </th>
              <SortableHeader
                label="종목명"
                sortKey="name"
                activeKey={sortKey}
                dir={sortDir}
                onSort={handleSort}
              />
              <SortableHeader
                label="현재가"
                sortKey="price"
                activeKey={sortKey}
                dir={sortDir}
                onSort={handleSort}
                align="right"
              />
              <SortableHeader
                label="충족 팩터"
                sortKey="factors"
                activeKey={sortKey}
                dir={sortDir}
                onSort={handleSort}
              />
              <SortableHeader
                label="상승 확률 π"
                sortKey="prob"
                activeKey={sortKey}
                dir={sortDir}
                onSort={handleSort}
              />
            </tr>
          </thead>
          <tbody>
            {sortedRows.map((row, index) => (
              <tr
                key={row.ticker}
                className="border-t border-[var(--border)]/80 transition-colors hover:bg-[var(--surface)]/50"
              >
                <td className="px-5 py-4 text-[var(--muted)] tabular-nums">
                  {index + 1}
                </td>
                <td className="px-5 py-4">
                  <div className="font-medium text-[var(--text)]">{row.name}</div>
                  <div className="mt-0.5 font-mono text-xs text-[var(--muted)]">
                    {row.ticker}
                  </div>
                </td>
                <td className="px-5 py-4 text-right font-medium tabular-nums">
                  {fmtPrice(row.price)}
                </td>
                <td className="px-5 py-4 align-top">
                  <FactorTags tags={row.factor_tags ?? []} />
                </td>
                <td className="px-5 py-4 align-top">
                  <PosteriorBar
                    prob={row.posterior_up_prob}
                    probPct={row.posterior_up_prob_pct}
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
