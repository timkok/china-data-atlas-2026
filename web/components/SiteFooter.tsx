import Link from "next/link";

export function SiteFooter({ generatedOn, coverage }: { generatedOn: string; coverage: string }) {
  return (
    <footer className="mt-16 border-t border-line">
      <div className="page-wrap grid gap-6 py-10 text-sm text-muted md:grid-cols-3">
        <p>{coverage}</p>
        <p>
          数据来自国家统计局《中国统计年鉴》公开表。构建日期 {generatedOn}。本站不在请求时抓取，也不用插值填补缺年。
        </p>
        <p className="flex flex-col gap-1">
          <Link href="/methodology" className="text-teal hover:underline">口径、修订与引用</Link>
          <Link href="/data" className="text-teal hover:underline">浏览并下载</Link>
          <a href="https://www.stats.gov.cn/sj/ndsj/" className="hover:underline">年鉴目录</a>
        </p>
      </div>
    </footer>
  );
}
