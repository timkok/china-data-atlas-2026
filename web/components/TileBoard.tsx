"use client";

import { TILE_COLORS, formatNumber, quantileBucket } from "@/lib/format";
import type { Region, RegionGroup } from "@/lib/types";

export function TileBoard({
  provinces,
  groups,
  values,
  decimals,
  unit,
  selected,
  onSelect,
  note,
}: {
  provinces: Region[];
  groups: RegionGroup[];
  values: Record<string, number | null>;
  decimals: number;
  unit: string;
  selected: string | null;
  onSelect: (code: string) => void;
  note: string;
}) {
  const byCode = Object.fromEntries(provinces.map((region) => [region.code, region]));
  const present = Object.values(values).filter((value): value is number => value !== null && value !== undefined);
  const sorted = [...present].sort((a, b) => a - b);
  return (
    <div>
      <p className="mb-3 text-sm text-muted">{note}</p>
      <div className="mb-4 flex flex-wrap items-center gap-3 text-xs text-muted" aria-hidden={present.length === 0}>
        <span>低</span>
        {TILE_COLORS.map((color) => (
          <span key={color} className="h-3 w-8 rounded-sm" style={{ background: color }} />
        ))}
        <span>高</span>
        {present.length > 0 && (
          <span>
            {formatNumber(sorted[0], decimals)} – {formatNumber(sorted[sorted.length - 1], decimals)} {unit}
          </span>
        )}
      </div>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {groups.map((group) => (
          <section key={group.id} aria-label={group.name_zh}>
            <h3 className="mb-2 text-sm font-medium text-deep">{group.name_zh}</h3>
            <div className="grid grid-cols-3 gap-1.5">
              {group.members.map((code) => {
                const region = byCode[code];
                const value = values[code];
                const missing = value === null || value === undefined;
                const bucket = missing ? -1 : quantileBucket(value, sorted);
                const background = missing ? "#ebe4d6" : TILE_COLORS[bucket];
                const color = !missing && bucket >= 3 ? "#f7f3ea" : "#1c2430";
                return (
                  <button
                    key={code}
                    type="button"
                    onClick={() => onSelect(code)}
                    aria-pressed={selected === code}
                    className={`rounded-md px-2 py-2 text-left text-xs leading-tight ${selected === code ? "ring-2 ring-clay" : ""}`}
                    style={{ background, color }}
                    data-region={code}
                    data-value={missing ? "" : value}
                  >
                    <span className="block font-medium">{region?.short}</span>
                    <span className="block tabular-nums">{missing ? "—" : formatNumber(value, decimals)}</span>
                  </button>
                );
              })}
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}
