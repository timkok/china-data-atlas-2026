import type { Metadata } from "next";
import "./globals.css";
import { I18nProvider } from "@/components/I18n";
import { SiteHeader } from "@/components/SiteHeader";
import { SiteFooter } from "@/components/SiteFooter";
import { getSummary, siteUrl } from "@/lib/data";

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl()),
  title: { default: "中国数据地图", template: "%s · 中国数据地图" },
  description: "国家统计局年鉴中的中国大陆分省年度统计。每个数字可回到来源表，缺年不插值。",
  openGraph: {
    title: "中国数据地图",
    description: "可核对的中国大陆省级统计。",
    locale: "zh_CN",
    type: "website",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const summary = getSummary();
  return (
    <html lang="zh-CN">
      <body className="font-sans antialiased">
        <I18nProvider>
          <SiteHeader summary={summary} />
          <main id="content">{children}</main>
          <SiteFooter generatedOn={summary.generated_on} coverage={summary.regions.coverage_note} />
        </I18nProvider>
      </body>
    </html>
  );
}
