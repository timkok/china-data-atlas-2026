import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { getIndicator, getSummary } from "@/lib/data";
import { formatValue } from "@/lib/format";

export function generateStaticParams() {
  return getSummary().regions.provinces.map((item) => ({ code: item.code }));
}

export function generateMetadata({ params }: { params: Promise<{ code: string }> }): Promise<Metadata> {
  return params.then(({ code }) => {
    const region = getSummary().regions.provinces.find((item) => item.code === code);
    return { title: region ? region.name_zh : "地区", description: region ? `${region.name_zh}的已入库省级指标最新值` : undefined };
  });
}

export default async function ProvincePage({ params }: { params: Promise<{ code: string }> }) {
  const { code } = await params;
  const summary = getSummary();
  const region = summary.regions.provinces.find((item) => item.code === code);
  if (!region) notFound();
  const macro = summary.regions.macro_regions.find((item) => item.members.includes(code));
  const nbs = summary.regions.nbs_regions.find((item) => item.members.includes(code));
  const rows = summary.indicators.map((card) => {
    const series = getIndicator(card.id).series[code] || [];
    const latest = series.length ? series[series.length - 1] : null;
    return { card, latest };
  });
  return (
    <article className="page-wrap py-10">
      <p className="kicker">{region.code} · {macro?.name_zh} · 统计局{nbs?.name_zh}</p>
      <h1 className="mt-2 font-serif text-4xl text-deep">{region.name_zh}</h1>
      <p className="mt-3 max-w-2xl leading-8">
        下面是各指标在本省（区、市）已入库序列中的最后一年。年份不同，是因为各表的最新公开年份不同，不是把某一年的空格补上了。
      </p>
      <table className="data mt-6 overflow-hidden rounded-2xl border border-line bg-card">
        <caption className="sr-only">{region.name_zh}各指标最新值</caption>
        <thead>
          <tr><th>指标</th><th>年</th><th>数值</th><th></th></tr>
        </thead>
        <tbody>
          {rows.map(({ card, latest }) => (
            <tr key={card.id}>
              <td>{card.name_zh}</td>
              <td>{latest ? latest.year : "—"}</td>
              <td className="tabular-nums">{latest ? formatValue(latest.value, card.decimals, card.unit) : "无分省数"}</td>
              <td>{latest ? <Link className="text-teal underline" href={`/indicators/${card.slug}?region=${code}&year=${latest.year}`}>打开</Link> : <Link className="text-teal underline" href={`/indicators/${card.slug}`}>说明</Link>}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </article>
  );
}
