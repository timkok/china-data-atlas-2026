import type { Metadata } from "next";
import Link from "next/link";
import { getSummary } from "@/lib/data";

export const metadata: Metadata = {
  title: "数据浏览与下载",
  description: "中国数据地图已入库指标的年份覆盖、缺测说明和 CSV 下载。",
};

export default function DataPage() {
  const summary = getSummary();
  return (
    <div className="page-wrap py-10">
      <p className="kicker">数据</p>
      <h1 className="mt-2 font-serif text-4xl text-deep">浏览与下载</h1>
      <p className="mt-4 max-w-3xl leading-8">
        全库 {summary.stats.observation_count.toLocaleString("zh-CN")} 条，构建于 {summary.generated_on}。
        CSV 含指标定义、单位、GB/T 2260 地区代码、年份、数值、发布机构、来源网址、表名、检索日期、状态、口径说明和加工方式。
      </p>
      <p className="mt-3">
        <a className="rounded-full bg-teal px-4 py-2 text-sm text-white" href="/downloads/all-observations.csv">下载全部观测</a>
      </p>
      <div className="mt-8 overflow-auto rounded-2xl border border-line bg-card">
        <table className="data">
          <thead>
            <tr>
              <th>指标</th><th>单位</th><th>年份</th><th>省级覆盖</th><th>观测</th><th>CSV</th>
            </tr>
          </thead>
          <tbody>
            {summary.indicators.map((item) => (
              <tr key={item.id}>
                <td><Link className="text-teal underline" href={`/indicators/${item.slug}`}>{item.name_zh}</Link></td>
                <td>{item.unit}</td>
                <td className="tabular-nums">{item.year_min}–{item.year_max}</td>
                <td>{item.geography === "national-only" ? "仅全国" : `${item.n_provinces} 个地区`}</td>
                <td className="tabular-nums">{item.n_obs}</td>
                <td><a className="text-teal underline" href={`/downloads/${item.id}.csv`}>下载</a></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <h2 className="mt-10 font-serif text-3xl">字段</h2>
      <ul className="mt-3 list-disc space-y-1 pl-5 text-sm leading-6">
        <li>indicator_id、name_zh、name_en、definition、unit</li>
        <li>region_code（省级为 GB/T 2260；000000 为全国合计，不是行政区代码）、region_name、year、value</li>
        <li>source_agency、source_url、source_table、publish_date、retrieval_date、status</li>
        <li>scope_note、processing、yearbook_year、source_kind、revision_flag、yoy、yoy_comparable</li>
      </ul>
      <p className="mt-4 text-sm leading-6 text-muted">{summary.regions.coverage_note}</p>
    </div>
  );
}
