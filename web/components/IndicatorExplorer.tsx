"use client";

import { useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { TrendChart } from "./TrendChart";
import { TileBoard } from "./TileBoard";
import { formatNumber, formatValue, formatYoy } from "@/lib/format";
import type { IndicatorFile, Summary } from "@/lib/types";

export function IndicatorExplorer({ data, summary }: { data: IndicatorFile; summary: Summary }) {
  const router = useRouter();
  const params = useSearchParams();
  const provinces = summary.regions.provinces;
  const years = useMemo(() => {
    const set = new Set<number>();
    Object.values(data.series).forEach((points) => points.forEach((point) => set.add(point.year)));
    return [...set].sort((a, b) => b - a);
  }, [data.series]);
  const defaultYear = useMemo(() => {
    const counts = new Map<number, number>();
    for (const [code, points] of Object.entries(data.series)) {
      if (code === "000000") continue;
      for (const point of points) counts.set(point.year, (counts.get(point.year) || 0) + 1);
    }
    let best = years[0] ?? null;
    let bestCount = -1;
    for (const [year, count] of counts) {
      if (count > bestCount || (count === bestCount && best !== null && year > best)) {
        best = year;
        bestCount = count;
      }
    }
    return best;
  }, [data.series, years]);

  const initialYear = Number(params.get("year")) || defaultYear;
  const initialRegion = params.get("region");
  const [year, setYear] = useState<number | null>(years.includes(initialYear) ? initialYear : defaultYear);
  const [region, setRegion] = useState<string | null>(initialRegion && data.series[initialRegion] ? initialRegion : provinces[0]?.code ?? null);
  const [group, setGroup] = useState("all");
  const [query, setQuery] = useState("");
  const [sort, setSort] = useState<"value" | "name" | "code">("value");

  function writeQuery(nextYear: number | null, nextRegion: string | null) {
    const search = new URLSearchParams();
    if (nextYear) search.set("year", String(nextYear));
    if (nextRegion) search.set("region", nextRegion);
    router.replace(`?${search.toString()}`, { scroll: false });
  }

  const nationalPoint = year ? (data.series["000000"] || []).find((point) => point.year === year) : undefined;
  const values: Record<string, number | null> = {};
  for (const province of provinces) {
    const point = year ? (data.series[province.code] || []).find((item) => item.year === year) : undefined;
    values[province.code] = point ? point.value : null;
  }
  const selectedPoint = region && year ? (data.series[region] || []).find((point) => point.year === year) : undefined;
  const selectedName = provinces.find((item) => item.code === region)?.name_zh ?? "全国";

  const memberSet = useMemo(() => {
    if (group === "all") return new Set(provinces.map((item) => item.code));
    if (group.startsWith("nbs:")) {
      const nbs = summary.regions.nbs_regions.find((item) => item.id === group.slice(4));
      return new Set(nbs?.members ?? []);
    }
    const macro = summary.regions.macro_regions.find((item) => item.id === group);
    return new Set(macro?.members ?? []);
  }, [group, provinces, summary.regions]);

  const ranked = provinces
    .filter((item) => memberSet.has(item.code) && values[item.code] !== null)
    .map((item) => ({ ...item, value: values[item.code] as number }))
    .sort((a, b) => b.value - a.value);

  const compareCodes = useMemo(() => {
    const defaults = ["110000", "310000", "440000", "410000", "510000", "540000"];
    const chosen = new Set<string>([...(region ? [region] : []), ...defaults]);
    return [...chosen].filter((code) => data.series[code]?.length).slice(0, 6);
  }, [region, data.series]);

  const trendYears = useMemo(() => {
    const set = new Set<number>();
    ["000000", ...compareCodes].forEach((code) => (data.series[code] || []).forEach((point) => set.add(point.year)));
    return [...set].sort((a, b) => a - b);
  }, [compareCodes, data.series]);

  const trendSeries = useMemo(() => [
    ...(data.series["000000"]
      ? [{
          name: "全国",
          data: trendYears.map((item) => data.series["000000"].find((point) => point.year === item)?.value ?? null),
        }]
      : []),
    ...compareCodes.map((code) => ({
      name: provinces.find((item) => item.code === code)?.short || code,
      data: trendYears.map((item) => (data.series[code] || []).find((point) => point.year === item)?.value ?? null),
    })),
  ], [compareCodes, data.series, provinces, trendYears]);

  const rows = provinces.flatMap((province) =>
    (data.series[province.code] || []).map((point) => ({
      ...point,
      region_code: province.code,
      region_name: province.name_zh,
    })),
  );
  const nationalRows = (data.series["000000"] || []).map((point) => ({ ...point, region_code: "000000", region_name: "全国" }));
  const filtered = [...nationalRows, ...rows].filter((row) => {
    const hay = `${row.region_name} ${row.region_code} ${row.year}`.includes(query.trim());
    const inGroup = row.region_code === "000000" || memberSet.has(row.region_code);
    return hay && inGroup;
  });
  filtered.sort((a, b) => {
    if (sort === "name") return a.region_name.localeCompare(b.region_name, "zh") || a.year - b.year;
    if (sort === "code") return a.region_code.localeCompare(b.region_code) || a.year - b.year;
    return b.value - a.value || a.year - b.year;
  });

  const presentCount = Object.values(values).filter((value) => value !== null).length;
  const absentCount = provinces.length - presentCount;
  const provincial = data.meta.geography !== "national-only";

  return (
    <div className="mt-8 space-y-12">
      <section aria-labelledby="dist-heading">
        <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
          <h2 id="dist-heading" className="font-serif text-3xl">同年分布</h2>
          <label className="text-sm text-muted">
            年份
            <select
              aria-label="年份"
              className="ml-2 rounded-md border border-line bg-card px-3 py-2"
              value={year ?? ""}
              onChange={(event) => {
                const next = Number(event.target.value);
                setYear(next);
                writeQuery(next, region);
              }}
            >
              {years.map((item) => (
                <option key={item} value={item}>{item}</option>
              ))}
            </select>
          </label>
        </div>
        <div className="grid gap-4 md:grid-cols-3">
          <article className="rounded-2xl border border-line bg-card p-4">
            <p className="text-xs text-muted">全国 · {year ?? "—"}</p>
            <p className="mt-2 font-serif text-3xl tabular-nums" data-testid="national-value">
              {nationalPoint ? formatValue(nationalPoint.value, data.meta.decimals, data.meta.unit) : "缺测"}
            </p>
            <p className="mt-2 text-sm text-muted">
              {nationalPoint?.yoy_comparable
                ? `${data.meta.yoy_label_zh} ${formatYoy(nationalPoint.yoy, true, data.meta.yoy_method)}`
                : "与上一年不可比或上一年缺测，不计算变化。"}
            </p>
          </article>
          <article className="rounded-2xl border border-line bg-card p-4 md:col-span-2">
            <p className="text-xs text-muted" data-testid="selected-province">{selectedName}</p>
            <p className="mt-2 font-serif text-3xl tabular-nums" data-testid="selected-value">
              {selectedPoint ? formatValue(selectedPoint.value, data.meta.decimals, data.meta.unit) : "这一年没有该地区的数字"}
            </p>
            {selectedPoint && (
              <p className="mt-2 text-sm">
                <a className="text-teal underline" href={selectedPoint.source_url}>{selectedPoint.source_table}</a>
              </p>
            )}
          </article>
        </div>
        <div className="mt-6">
          {provincial ? (
            <TileBoard
              provinces={provinces}
              groups={summary.regions.macro_regions}
              values={values}
              decimals={data.meta.decimals}
              unit={data.meta.unit}
              selected={region}
              note="按华北、东北、华东、华中、华南、西南、西北排列。这不是地图，没有边界线。"
              onSelect={(code) => {
                setRegion(code);
                writeQuery(year, code);
              }}
            />
          ) : (
            <p className="rounded-2xl border border-dashed border-line bg-card p-6 text-sm leading-7" data-testid="no-province-data">
              {data.meta.geography_note || "年鉴的机器可读表没有公布分省序列，因此这里不画省。全国序列仍在上方和下方的表里。"}
            </p>
          )}
        </div>
      </section>

      <section aria-labelledby="trend-heading">
        <h2 id="trend-heading" className="font-serif text-3xl">历史走势</h2>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-muted">
          断线就是缺年，没有把缺口连起来。红色虚线是登记过的口径或普查年份。若相邻两年出自不同年鉴版本，变化率留空。
        </p>
        <div className="mt-4 rounded-2xl border border-line bg-card p-3">
          <TrendChart
            categories={trendYears}
            series={trendSeries}
            breaks={(data.meta.breaks || []).map((item) => item.year)}
            unit={data.meta.unit}
          />
        </div>
      </section>

      <section aria-labelledby="rank-heading">
        <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
          <h2 id="rank-heading" className="font-serif text-3xl">排名</h2>
          <label className="text-sm text-muted">
            范围
            <select aria-label="地区范围" className="ml-2 rounded-md border border-line bg-card px-3 py-2" value={group} onChange={(event) => setGroup(event.target.value)}>
              <option value="all">全部省级地区</option>
              <optgroup label="七大地理区">
                {summary.regions.macro_regions.map((item) => (
                  <option key={item.id} value={item.id}>{item.name_zh}</option>
                ))}
              </optgroup>
              <optgroup label="统计局东中西东北">
                {summary.regions.nbs_regions.map((item) => (
                  <option key={`nbs-${item.id}`} value={`nbs:${item.id}`}>{item.name_zh}</option>
                ))}
              </optgroup>
            </select>
          </label>
        </div>
        {data.meta.national_benchmark_line && nationalPoint && (
          <p className="mb-3 text-sm text-muted">全国 {formatNumber(nationalPoint.value, data.meta.decimals)} {data.meta.unit}，在下图中作为参照线。总量指标的全国数远大于任何一省，故不画这条线。</p>
        )}
        <ol className="space-y-1" data-testid="rank-list">
          {ranked.map((item, index) => {
            const width = ranked[0] ? Math.max(4, (item.value / ranked[0].value) * 100) : 0;
            return (
              <li key={item.code}>
                <button
                  type="button"
                  onClick={() => {
                    setRegion(item.code);
                    writeQuery(year, item.code);
                  }}
                  className="grid w-full grid-cols-[2rem_4.5rem_1fr_auto] items-center gap-2 text-left text-sm"
                  data-rank-value={item.value}
                  data-region={item.code}
                >
                  <span className="tabular-nums text-muted">{index + 1}</span>
                  <span>{item.short}</span>
                  <span className="h-2 rounded-full bg-teal/80" style={{ width: `${width}%` }} />
                  <span className="tabular-nums">{formatNumber(item.value, data.meta.decimals)}</span>
                </button>
              </li>
            );
          })}
        </ol>
        {ranked.length === 0 && <p className="text-sm text-muted">这一年、这个范围内没有分省数字。</p>}
      </section>

      <section aria-labelledby="compare-heading">
        <h2 id="compare-heading" className="font-serif text-3xl">地区比较</h2>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-muted">
          走势图同时画出全国和最多六个省级地区。七大地理区和统计局四区只用于筛选，不把成员平均成一个官方地区数。
          {data.meta.additive ? " 该指标可以加总，但页面仍给出各省原值，避免把加总误写成国家统计局的地区汇总数。" : " 该指标不可加总，页面不提供各省合计。"}
        </p>
        <p className="mt-3 text-sm">当前对照：{compareCodes.map((code) => provinces.find((item) => item.code === code)?.short).filter(Boolean).join("、")}</p>
      </section>

      <section aria-labelledby="table-heading">
        <div className="mb-3 flex flex-wrap items-end justify-between gap-3">
          <div>
            <h2 id="table-heading" className="font-serif text-3xl">数据表</h2>
            <p className="mt-1 text-sm text-muted">
              {year} 年有数的省级地区 {presentCount} 个，缺测 {absentCount} 个。全表 {filtered.length} 行。
            </p>
          </div>
          <a className="rounded-full bg-teal px-4 py-2 text-sm text-white" href={`/downloads/${data.meta.id}.csv`} data-testid="csv-link">
            下载 CSV
          </a>
        </div>
        <div className="mb-3 flex flex-wrap gap-2">
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="筛选地区或年份" aria-label="筛选数据表" className="rounded-md border border-line bg-card px-3 py-2 text-sm" />
          <select aria-label="排序" value={sort} onChange={(event) => setSort(event.target.value as "value" | "name" | "code")} className="rounded-md border border-line bg-card px-3 py-2 text-sm">
            <option value="value">按数值</option>
            <option value="name">按地区</option>
            <option value="code">按代码</option>
          </select>
        </div>
        <div className="max-h-[32rem] overflow-auto rounded-2xl border border-line bg-card">
          <table className="data">
            <caption className="sr-only">{data.meta.name_zh}全部入库数值</caption>
            <thead>
              <tr>
                <th>地区</th>
                <th>代码</th>
                <th>年</th>
                <th>数值</th>
                <th>变化</th>
                <th>来源</th>
              </tr>
            </thead>
            <tbody>
              {filtered.slice(0, 400).map((row) => (
                <tr key={`${row.region_code}-${row.year}`} data-testid={row.region_code === region && row.year === year ? "selected-row" : undefined}>
                  <td>{row.region_name}</td>
                  <td className="tabular-nums">{row.region_code}</td>
                  <td className="tabular-nums">{row.year}</td>
                  <td className="tabular-nums" data-cell-value={row.value}>{formatNumber(row.value, data.meta.decimals)}</td>
                  <td>{row.yoy_comparable ? formatYoy(row.yoy, true, data.meta.yoy_method) : "—"}</td>
                  <td><a className="text-teal underline" href={row.source_url}>{row.yearbook_year}</a></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {filtered.length > 400 && <p className="mt-2 text-xs text-muted">页面先显示 400 行，完整序列在 CSV 里。</p>}
      </section>
    </div>
  );
}
