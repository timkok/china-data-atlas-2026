export type Lang = "zh" | "en";

export type Point = {
  year: number;
  value: number;
  yoy: number | null;
  yoy_comparable: boolean;
  yearbook_year: number;
  source_url: string;
  source_table: string;
  scope_note: string;
  status: string;
  processing: string;
  source_kind: string;
  revision_flag: boolean;
  publish_date: string;
  retrieval_date: string;
  source_agency: string;
};

export type IndicatorMeta = {
  id: string;
  slug: string;
  category: string;
  name_zh: string;
  name_en: string;
  definition: string;
  unit: string;
  decimals: number;
  yoy_method: string;
  yoy_label_zh: string;
  national_benchmark_line: boolean;
  additive: boolean;
  geography?: string;
  geography_note?: string;
  series_start_note?: string;
  processing?: string;
  breaks?: { year: number; note: string }[];
  related?: string[];
};

export type IndicatorCard = {
  id: string;
  slug: string;
  category: string;
  name_zh: string;
  name_en: string;
  unit: string;
  decimals: number;
  definition: string;
  geography: string;
  geography_note: string;
  series_start_note: string;
  year_min: number | null;
  year_max: number | null;
  n_obs: number;
  n_provinces: number;
  latest_national: { year: number; value: number } | null;
  latest_slice: { year: number; values: Record<string, number> } | null;
  related: string[];
  yoy_label_zh: string;
  national_benchmark_line: boolean;
  additive: boolean;
};

export type Region = {
  code: string;
  name_zh: string;
  name_en: string;
  short: string;
  macro: string | null;
  nbs: string | null;
};

export type RegionGroup = { id: string; name_zh: string; name_en: string; members: string[] };

export type Summary = {
  generated_on: string;
  categories: { id: string; name_zh: string; name_en: string; summary_zh: string }[];
  indicators: IndicatorCard[];
  findings: { indicator_id: string; year: number; text: string }[];
  regions: {
    national: Region;
    provinces: Region[];
    macro_regions: RegionGroup[];
    nbs_regions: RegionGroup[];
    coverage_note: string;
  };
  stats: { indicator_count: number; observation_count: number; province_count: number; source_agency: string };
};

export type IndicatorFile = {
  meta: IndicatorMeta;
  sources: { yearbook_year: number; source_table: string; source_url: string; n: number }[];
  series: Record<string, Point[]>;
  year_min: number | null;
  year_max: number | null;
  n_obs: number;
  n_provinces: number;
};
