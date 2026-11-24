import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Suspense } from "react";
import { IndicatorExplorer } from "@/components/IndicatorExplorer";
import { getIndicator, getSummary } from "@/lib/data";
import { formatValue } from "@/lib/format";

export function generateStaticParams() {
  return getSummary().indicators.map((item) => ({ slug: item.slug }));
}

export function generateMetadata({ params }: { params: Promise<{ slug: string }> }): Promise<Metadata> {
  return params.then(({ slug }) => {
    const card = getSummary().indicators.find((item) => item.slug === slug);
    if (!card) return { title: "未找到指标" };
    const latest = card.latest_national
      ? `最新全国值 ${formatValue(card.latest_national.value, card.decimals, card.unit)}（${card.latest_national.year}）`
      : "分省序列";
    return {
      title: card.name_zh,
      description: `${card.name_zh}（${card.name_en}）。${card.definition} ${latest}`,
      openGraph: { title: `${card.name_zh} · 中国数据地图`, description: card.definition },
    };
  });
}

export default async function IndicatorPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const summary = getSummary();
  const card = summary.indicators.find((item) => item.slug === slug);
  if (!card) notFound();
  const data = getIndicator(card.id);
  const related = summary.indicators.filter((item) => card.related.includes(item.id));
  const citation = `中国数据地图. ${card.name_zh}[${card.unit}]. 数据构建于 ${summary.generated_on}. 来源: 国家统计局《中国统计年鉴》.`;
  return (
    <article className="page-wrap py-8">
      <p className="kicker">{summary.categories.find((item) => item.id === card.category)?.name_zh}</p>
      <h1 className="mt-2 font-serif text-4xl text-deep md:text-5xl">{card.name_zh}</h1>
      <p className="mt-2 text-muted">{card.name_en} · 单位 {card.unit}</p>
      <p className="mt-5 max-w-3xl text-lg leading-8">{card.definition}</p>
      {card.series_start_note && <p className="mt-3 max-w-3xl text-sm leading-6 text-muted">{card.series_start_note}</p>}
      <p className="mt-4 text-sm">
        入库 {card.year_min}–{card.year_max} 年，{card.n_obs.toLocaleString("zh-CN")} 条。
        {card.latest_national && (
          <> 全国最近一条是 {card.latest_national.year} 年的 {formatValue(card.latest_national.value, card.decimals, card.unit)}。</>
        )}
      </p>
      <Suspense fallback={<p className="mt-8 text-sm text-muted">正在载入图表…</p>}>
        <IndicatorExplorer data={data} summary={summary} />
      </Suspense>
      <section className="mt-14" aria-labelledby="method-heading">
        <h2 id="method-heading" className="font-serif text-3xl">口径、加工与引用</h2>
        <p className="mt-3 max-w-3xl leading-8">{card.definition}</p>
        {data.meta.processing && <p className="mt-3 max-w-3xl leading-8">{data.meta.processing}</p>}
        <ul className="mt-4 list-disc space-y-2 pl-5 text-sm leading-6">
          {(data.meta.breaks || []).map((item) => (
            <li key={item.year}><strong>{item.year} 年。</strong> {item.note}</li>
          ))}
        </ul>
        {card.geography_note && <p className="mt-4 max-w-3xl text-sm leading-6">{card.geography_note}</p>}
        <h3 className="mt-6 font-serif text-2xl">来源表</h3>
        <ul className="mt-2 space-y-1 text-sm">
          {data.sources.slice(0, 12).map((source) => (
            <li key={source.source_url + source.n}>
              <a className="text-teal underline" href={source.source_url}>{source.source_table}</a>
              <span className="text-muted"> · {source.n} 条</span>
            </li>
          ))}
        </ul>
        <p className="mt-4 text-sm leading-6 text-muted">状态多为「未知」：年鉴格内通常不写初步或最终。出版日未印在表上，故不填写。检索日期是数据构建日 {summary.generated_on}。</p>
        <h3 className="mt-6 font-serif text-2xl">建议引用</h3>
        <blockquote className="mt-2 border-l-2 border-teal pl-4 text-sm leading-6">{citation}</blockquote>
        {related.length > 0 && (
          <>
            <h3 className="mt-6 font-serif text-2xl">相关指标</h3>
            <ul className="mt-2 flex flex-wrap gap-3 text-sm">
              {related.map((item) => (
                <li key={item.id}><Link className="text-teal underline" href={`/indicators/${item.slug}`}>{item.name_zh}</Link></li>
              ))}
            </ul>
          </>
        )}
        <p className="mt-6 text-sm"><Link className="text-teal underline" href="/methodology">全站方法说明</Link></p>
      </section>
    </article>
  );
}
