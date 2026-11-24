import fs from "fs";
import path from "path";
import type { IndicatorFile, Summary } from "./types";

const dataDir = path.join(process.cwd(), "data");

export function getSummary(): Summary {
  return JSON.parse(fs.readFileSync(path.join(dataDir, "summary.json"), "utf8")) as Summary;
}

export function getIndicator(id: string): IndicatorFile {
  const file = path.join(dataDir, "indicators", `${id}.json`);
  return JSON.parse(fs.readFileSync(file, "utf8")) as IndicatorFile;
}

export function siteUrl(): string {
  return process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000";
}
