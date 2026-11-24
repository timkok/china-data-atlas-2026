"use client";

import { useEffect, useRef } from "react";
import type { ECharts } from "echarts";

export function TrendChart({
  categories,
  series,
  breaks,
  unit,
}: {
  categories: number[];
  series: { name: string; data: (number | null)[] }[];
  breaks: number[];
  unit: string;
}) {
  const host = useRef<HTMLDivElement>(null);
  const chart = useRef<ECharts | null>(null);

  useEffect(() => {
    let disposed = false;
    (async () => {
      const echarts = await import("echarts");
      if (disposed || !host.current) return;
      chart.current?.dispose();
      const instance = echarts.init(host.current);
      chart.current = instance;
      instance.setOption({
        color: ["#0f5c56", "#b5522a", "#1c2430", "#a37b2c", "#3d6f9a", "#6b4c7a"],
        tooltip: { trigger: "axis" },
        legend: { type: "scroll", bottom: 0, textStyle: { color: "#5c6670" } },
        grid: { left: 48, right: 16, top: 24, bottom: 48 },
        xAxis: { type: "category", data: categories, axisLabel: { color: "#5c6670" } },
        yAxis: { type: "value", name: unit, nameTextStyle: { color: "#5c6670" }, axisLabel: { color: "#5c6670" }, splitLine: { lineStyle: { color: "#eadfce" } } },
        series: series.map((item) => ({
          name: item.name,
          type: "line",
          showSymbol: false,
          connectNulls: false,
          data: item.data,
          markLine: breaks.length
            ? {
                symbol: "none",
                label: { formatter: "口径", color: "#b5522a" },
                lineStyle: { color: "#b5522a", type: "dashed" },
                data: breaks.filter((year) => categories.includes(year)).map((year) => ({ xAxis: String(year) })),
              }
            : undefined,
        })),
      });
    })();
    const onResize = () => chart.current?.resize();
    window.addEventListener("resize", onResize);
    return () => {
      disposed = true;
      window.removeEventListener("resize", onResize);
      chart.current?.dispose();
      chart.current = null;
    };
  }, [categories, series, breaks, unit]);

  return <div ref={host} className="h-80 w-full" role="img" aria-label="历史走势图" />;
}
