"use client";

import { useState } from "react";
import Link from "next/link";
import { TileBoard } from "./TileBoard";
import { formatValue } from "@/lib/format";
import type { Summary } from "@/lib/types";

const FEATURED = ["population", "gdp-per-capita", "disposable-income", "urbanization"];

export function HomeBoard({ summary }: { summary: Summary }) {
  const options = summary.indicators.filter((item) => FEATURED.includes(item.id) && item.latest_slice);
  const [id, setId] = useState(options[0]?.id ?? "population");
  const [selected, setSelected] = useState<string | null>(null);
  const card = options.find((item) => item.id === id) ?? options[0];
  if (!card?.latest_slice) return null;
  const values = Object.fromEntries(summary.regions.provinces.map((region) => [region.code, card.latest_slice?.values[region.code] ?? null]));
  const region = summary.regions.provinces.find((item) => item.code === selected);
  const selectedValue = selected ? card.latest_slice.values[selected] : undefined;
  return (
    <section aria-labelledby="board-heading" className="mt-14">
      <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 id="board-heading" className="font-serif text-3xl">先看一年</h2>
          <p className="mt-1 text-sm text-muted">瓦片只表示数值高低，不画省界。点一个省，再进指标页看全部年份。</p>
        </div>
        <label className="text-sm">
          指标
          <select aria-label="首页指标" className="ml-2 rounded-md border border-line bg-card px-3 py-2" value={card.id} onChange={(event) => { setId(event.target.value); setSelected(null); }}>
            {options.map((item) => (
              <option key={item.id} value={item.id}>{item.name_zh}</option>
            ))}
          </select>
        </label>
      </div>
      <p className="mb-4 text-sm">
        {card.name_zh} · {card.latest_slice.year} 年
        {card.latest_national && card.latest_national.year === card.latest_slice.year && (
          <> · 全国 {formatValue(card.latest_national.value, card.decimals, card.unit)}</>
        )}
        {region && selectedValue !== undefined && (
          <> · {region.name_zh} {formatValue(selectedValue, card.decimals, card.unit)}</>
        )}
      </p>
      <TileBoard
        provinces={summary.regions.provinces}
        groups={summary.regions.macro_regions}
        values={values}
        decimals={card.decimals}
        unit={card.unit}
        selected={selected}
        onSelect={setSelected}
        note="分组是华北到西北的阅读顺序，不是地理位置的投影。"
      />
      <p className="mt-4 text-sm">
        <Link className="text-teal underline" href={`/indicators/${card.slug}?year=${card.latest_slice.year}${selected ? `&region=${selected}` : ""}`}>
          打开{card.name_zh}的完整年份、排名和来源
        </Link>
      </p>
    </section>
  );
}
