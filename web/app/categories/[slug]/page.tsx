import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { getSummary } from "@/lib/data";
import { formatValue } from "@/lib/format";

export function generateStaticParams() {
  return getSummary().categories.map((item) => ({ slug: item.id }));
}

export function generateMetadata({ params }: { params: Promise<{ slug: string }> }): Promise<Metadata> {
  return params.then(({ slug }) => {
    const category = getSummary().categories.find((item) => item.id === slug);
    return { title: category ? category.name_zh : "主题", description: category?.summary_zh };
  });
}

export default async function CategoryPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const summary = getSummary();
  const category = summary.categories.find((item) => item.id === slug);
  if (!category) notFound();
  const items = summary.indicators.filter((item) => item.category === category.id);
  return (
    <div className="page-wrap py-10">
      <p className="kicker">主题</p>
      <h1 className="mt-2 font-serif text-4xl text-deep">{category.name_zh}</h1>
      <p className="mt-3 max-w-2xl text-lg leading-8">{category.summary_zh}</p>
      <ul className="mt-8 divide-y divide-line rounded-2xl border border-line bg-card">
        {items.map((item) => (
          <li key={item.id} className="px-5 py-4">
            <Link href={`/indicators/${item.slug}`} className="font-serif text-2xl text-deep hover:text-teal">{item.name_zh}</Link>
            <p className="mt-1 text-sm text-muted">{item.name_en} · {item.year_min}–{item.year_max} · {item.n_provinces} 个省级地区</p>
            <p className="mt-2 text-sm leading-6">{item.definition}</p>
            {item.latest_national && (
              <p className="mt-2 text-sm">全国最近值 {formatValue(item.latest_national.value, item.decimals, item.unit)}（{item.latest_national.year}）</p>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
