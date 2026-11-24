"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { useI18n } from "./I18n";
import type { Summary } from "@/lib/types";

export function SearchBox({ summary }: { summary: Summary }) {
  const { t } = useI18n();
  const [query, setQuery] = useState("");
  const results = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return [];
    const indicators = summary.indicators
      .filter((item) => `${item.name_zh} ${item.name_en} ${item.id}`.toLowerCase().includes(q))
      .slice(0, 6)
      .map((item) => ({ href: `/indicators/${item.slug}`, label: item.name_zh, hint: item.name_en }));
    const provinces = summary.regions.provinces
      .filter((item) => `${item.name_zh} ${item.name_en} ${item.short}`.toLowerCase().includes(q))
      .slice(0, 6)
      .map((item) => ({ href: `/provinces/${item.code}`, label: item.name_zh, hint: item.name_en }));
    return [...indicators, ...provinces].slice(0, 8);
  }, [query, summary]);

  return (
    <div className="relative min-w-[220px] flex-1 sm:max-w-xs">
      <label htmlFor="site-search" className="sr-only">{t.search}</label>
      <input
        id="site-search"
        value={query}
        onChange={(event) => setQuery(event.target.value)}
        placeholder={t.search}
        className="w-full rounded-full border border-line bg-card px-4 py-2 text-sm"
        autoComplete="off"
      />
      {results.length > 0 && (
        <ul className="absolute left-0 right-0 top-11 z-40 overflow-hidden rounded-2xl border border-line bg-card shadow-lg" role="listbox">
          {results.map((item) => (
            <li key={item.href}>
              <Link href={item.href} className="block px-4 py-2 hover:bg-paper" onClick={() => setQuery("")}>
                <span className="block text-sm">{item.label}</span>
                <span className="text-xs text-muted">{item.hint}</span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
