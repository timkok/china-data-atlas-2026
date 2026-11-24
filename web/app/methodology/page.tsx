import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "方法与关于数据",
  description: "中国数据地图的来源、加工、口径变化、地图决定和引用方式。",
};

export default function MethodologyPage() {
  return (
    <article className="page-wrap prose-stat py-10">
      <p className="kicker">方法</p>
      <h1 className="mt-2 font-serif text-4xl text-deep">关于这些数字</h1>
      <h2 className="mt-8 font-serif text-2xl">从哪来</h2>
      <p>
        来源是国家统计局《中国统计年鉴》公开表。约 2005–2014 年以及 2021 年的目标表有 Excel，流水线直接读原表。
        2015–2020 年和 2022–2025 年的数据表在年鉴网站上是 JPG。其中 2025 年鉴里人口、城镇化、居民收入、社会消费品零售总额和地区生产总值，由人工对照印本录入，文件在 <code>data/manual/</code>，自动抓取不会覆盖。
      </p>
      <p>
        国家数据 data.stats.gov.cn 的分省年度库在构建环境返回 403（UrlACL）。没有尝试绕过，也没有用其他网站的转载数填空。
      </p>
      <h2 className="mt-8 font-serif text-2xl">怎么加工</h2>
      <p>
        同一指标、同一地区、同一年如果出现在多本年鉴里，保留年鉴年份较新的一条，并标记与旧版差异较大的修订。
        相邻两年若出自不同年鉴版本，或者跨过登记的口径年份，页面不计算变化率。
        不插值。65 岁及以上占比只在同一张表内用人数相除。人均地区生产总值只用年鉴直接公布的列；2024 年的人均数还要用同年年末人口做数量级核对，对不上就不入库。
      </p>
      <h2 className="mt-8 font-serif text-2xl">口径上不能混的几件事</h2>
      <p>分地区人口从 2005 年起年鉴才称为常住人口。全国人口含现役军人，分省不含，所以各省加总不能拿来核对全国。</p>
      <p>地区生产总值是现价。各省之和不等于国内生产总值。现价水平的同比也不是年鉴里的实际增速指数，指数单独成一个指标。</p>
      <p>居民人均可支配收入从住户调查一体化之后起算，不与更早的城镇可支配收入或农村纯收入拼接。</p>
      <p>普通高校在校生和学校数不含 2022 年起「普通、职业」合并发表的表。</p>
      <p>年龄结构有的年份是普查，有的年份是抽样调查，图上会断开。</p>
      <h2 className="mt-8 font-serif text-2xl">地区分组</h2>
      <p>
        七大地理区：华北（北京、天津、河北、山西、内蒙古），东北（辽宁、吉林、黑龙江），华东（上海、江苏、浙江、安徽、福建、江西、山东），华中（河南、湖北、湖南），华南（广东、广西、海南），西南（重庆、四川、贵州、云南、西藏），西北（陕西、甘肃、青海、宁夏、新疆）。
      </p>
      <p>
        统计局东、中、西、东北是另一套，用于住户调查等发布。内蒙古在这套里属西部，不在东北，也不在华北。筛选时两套分组不会混在一个平均数里。不可加总的指标不提供「地区合计」。
      </p>
      <h2 className="mt-8 font-serif text-2xl">为什么没有地图</h2>
      <p>
        公开的全国分省填色图需要地图审核。标准地图改填色不能沿用原审图号。本站没有审图号，因此不画省界。正式浏览是分区瓦片和排名。决定写在 <Link href="/methodology" className="text-teal underline">本页</Link>，仓库里的说明是 <code>docs/map-compliance.md</code>。
      </p>
      <h2 className="mt-8 font-serif text-2xl">没有覆盖的地方</h2>
      <p>香港、澳门、台湾不在本产品的统计范围内。页面上的空缺不是关于领土的表述。</p>
      <h2 className="mt-8 font-serif text-2xl">引用</h2>
      <p>中国数据地图。指标名称。构建日期。来源：国家统计局《中国统计年鉴》相应表。</p>
      <p className="text-sm text-muted">以后若做多指标对照或只依据本表回答问题的助手，计算必须带来源、年份和公式，相关不等于因果。这一版没有接入任何模型。</p>
    </article>
  );
}
