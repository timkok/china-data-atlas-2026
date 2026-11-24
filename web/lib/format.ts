export function formatNumber(value: number, decimals: number): string {
  return value.toLocaleString("zh-CN", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

export function formatValue(value: number, decimals: number, unit: string): string {
  return `${formatNumber(value, decimals)} ${unit}`;
}

export function formatYoy(value: number | null, comparable: boolean, method: string): string {
  if (!comparable || value === null || Number.isNaN(value)) return "—";
  const sign = value > 0 ? "+" : "";
  const digits = method === "pct" ? 1 : 2;
  return `${sign}${value.toLocaleString("zh-CN", { minimumFractionDigits: digits, maximumFractionDigits: digits })}`;
}

export function quantileBucket(value: number, sorted: number[], buckets = 5): number {
  if (sorted.length === 0) return 0;
  const below = sorted.filter((item) => item < value).length;
  return Math.min(buckets - 1, Math.floor((below / sorted.length) * buckets));
}

export const TILE_COLORS = ["#d7ebe6", "#9dcec6", "#4eaaa0", "#1f7368", "#0d3f3b"];
