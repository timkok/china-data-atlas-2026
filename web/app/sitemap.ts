import type { MetadataRoute } from "next";
import { getSummary, siteUrl } from "@/lib/data";

export default function sitemap(): MetadataRoute.Sitemap {
  const base = siteUrl();
  const summary = getSummary();
  const now = new Date(summary.generated_on);
  const staticRoutes = ["", "/data", "/methodology"].map((path) => ({
    url: `${base}${path || "/"}`,
    lastModified: now,
  }));
  const categories = summary.categories.map((item) => ({ url: `${base}/categories/${item.id}`, lastModified: now }));
  const indicators = summary.indicators.map((item) => ({ url: `${base}/indicators/${item.slug}`, lastModified: now }));
  const provinces = summary.regions.provinces.map((item) => ({ url: `${base}/provinces/${item.code}`, lastModified: now }));
  return [...staticRoutes, ...categories, ...indicators, ...provinces];
}
