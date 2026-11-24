"use client";

import Link from "next/link";
import { useI18n } from "./I18n";
import { SearchBox } from "./SearchBox";
import type { Summary } from "@/lib/types";

export function SiteHeader({ summary }: { summary: Summary }) {
  const { t, toggle } = useI18n();
  return (
    <header className="sticky top-0 z-30 border-b border-line/80 bg-paper/90 backdrop-blur">
      <a href="#content" className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-2 focus:bg-card focus:px-3 focus:py-2">
        跳到正文
      </a>
      <div className="page-wrap flex flex-wrap items-center gap-x-6 gap-y-3 py-3">
        <Link href="/" className="min-w-[10rem]">
          <span className="block font-serif text-xl leading-none text-deep">{t.brand}</span>
          <span className="text-xs text-muted">{t.brandEn}</span>
        </Link>
        <nav className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm" aria-label="主导航">
          <Link href="/" className="hover:text-teal">{t.home}</Link>
          {summary.categories.map((category) => (
            <Link key={category.id} href={`/categories/${category.id}`} className="hover:text-teal">
              {category.name_zh}
            </Link>
          ))}
          <Link href="/data" className="hover:text-teal">{t.data}</Link>
          <Link href="/methodology" className="hover:text-teal">{t.method}</Link>
        </nav>
        <div className="ml-auto flex w-full items-center gap-3 sm:w-auto">
          <SearchBox summary={summary} />
          <button type="button" onClick={toggle} className="shrink-0 rounded-full border border-line px-3 py-1 text-xs text-muted">
            {t.lang}
          </button>
        </div>
      </div>
    </header>
  );
}
