import Link from "next/link";
import { HomeBoard } from "@/components/HomeBoard";
import { getSummary } from "@/lib/data";
import { formatValue } from "@/lib/format";

export default function HomePage() {
  const summary = getSummary();
  return (
    <div className="page-wrap pb-8">
      <section className="pt-10 md:pt-16">
        <p className="kicker">国家统计局年鉴 · 分省年度</p>
        <h1 className="mt-3 max-w-3xl font-serif text-4xl leading-tight text-deep md:text-6xl">
          把中国分省统计变得能读、能核、能接着查
        </h1>
        <p className="mt-5 max-w-2xl text-lg leading-8 text-ink/90">
          中国数据地图整理大陆 31 个省级地区的公开年度数字。指标页同时给出当年分布、历年走势、排名和原表链接。没有的年份留白，不把相邻点连成一条并不存在的曲线。
        </p>
        <p className="mt-4 max-w-2xl text-sm leading-6 text-muted">{summary.regions.coverage_note}</p>
        <dl className="mt-8 grid grid-cols-3 gap-3 text-sm md:max-w-xl">
          <div className="rounded-2xl border border-line bg-card px-4 py-3">
            <dt className="text-muted">指标</dt>
            <dd className="font-serif text-2xl">{summary.stats.indicator_count}</dd>
          </div>
          <div className="rounded-2xl border border-line bg-card px-4 py-3">
            <dt className="text-muted">观测</dt>
            <dd className="font-serif text-2xl">{summary.stats.observation_count.toLocaleString("zh-CN")}</dd>
          </div>
          <div className="rounded-2xl border border-line bg-card px-4 py-3">
            <dt className="text-muted">省级地区</dt>
            <dd className="font-serif text-2xl">{summary.stats.province_count}</dd>
          </div>
        </dl>
      </section>

      <section className="mt-12" aria-labelledby="cats-heading">
        <h2 id="cats-heading" className="font-serif text-3xl">从四个主题进去</h2>
        <div className="mt-4 grid gap-3 md:grid-cols-4">
          {summary.categories.map((category) => (
            <Link key={category.id} href={`/categories/${category.id}`} className="rounded-2xl border border-line bg-card p-4 hover:border-teal">
              <h3 className="font-serif text-2xl text-deep">{category.name_zh}</h3>
              <p className="mt-2 text-sm leading-6 text-muted">{category.summary_zh}</p>
              <p className="mt-3 text-sm text-teal">{summary.indicators.filter((item) => item.category === category.id).length} 个指标</p>
            </Link>
          ))}
        </div>
      </section>

      <HomeBoard summary={summary} />

      <section className="mt-14" aria-labelledby="findings-heading">
        <h2 id="findings-heading" className="font-serif text-3xl">从现有数字里能直接读出的话</h2>
        <div className="mt-4 space-y-4">
          {summary.findings.map((finding) => (
            <article key={finding.text} className="rounded-2xl border border-line bg-card p-5">
              <p className="text-lg leading-8">{finding.text}</p>
              <Link href={`/indicators/${finding.indicator_id}`} className="mt-2 inline-block text-sm text-teal underline">查看这个指标</Link>
            </article>
          ))}
        </div>
      </section>

      <section className="mt-14 grid gap-8 md:grid-cols-2" aria-labelledby="updated-heading">
        <div>
          <h2 id="updated-heading" className="font-serif text-3xl">最近的年份</h2>
          <ul className="mt-4 divide-y divide-line rounded-2xl border border-line bg-card">
            {[...summary.indicators].sort((a, b) => (b.year_max ?? 0) - (a.year_max ?? 0)).map((item) => (
              <li key={item.id} className="flex items-baseline justify-between gap-3 px-4 py-3">
                <Link href={`/indicators/${item.slug}`} className="hover:text-teal">{item.name_zh}</Link>
                <span className="text-sm text-muted">
                  {item.year_min}–{item.year_max}
                  {item.latest_national ? ` · 全国 ${formatValue(item.latest_national.value, item.decimals, item.unit)}` : ""}
                </span>
              </li>
            ))}
          </ul>
        </div>
        <div>
          <h2 className="font-serif text-3xl">来源与范围</h2>
          <p className="mt-4 leading-8">
            数字来自国家统计局《中国统计年鉴》的 Excel 原表，以及 2025 年鉴中尚无 Excel、经人工核对后录入的印本表。国家数据网站在构建环境被拒绝访问，没有改用未核对的转载数。
          </p>
          <p className="mt-3 leading-8">
            构建于 {summary.generated_on}，共 {summary.stats.observation_count.toLocaleString("zh-CN")} 条观测。每条都带表名和网址。
          </p>
          <p className="mt-4">
            <Link href="/data" className="text-teal underline">浏览全部指标并下载</Link>
          </p>
        </div>
      </section>
    </div>
  );
}
