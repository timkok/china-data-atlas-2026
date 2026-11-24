"""Standardize yearbook extracts and manual transcriptions into the publishable dataset."""

from __future__ import annotations

import importlib.util
import json
from datetime import date
from pathlib import Path

import duckdb
import pandas as pd
import yaml

from pipeline.extract import extract_frame, read_workbook
from pipeline.regions import BY_CODE, MACRO_REGIONS, NATIONAL, NBS_REGIONS, REGIONS

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "yearbook"
MANUAL = ROOT / "data" / "manual"
PROCESSED = ROOT / "data" / "processed"
WEB_DATA = ROOT / "web" / "data"
PUBLIC_DL = ROOT / "web" / "public" / "downloads"
RETRIEVAL_DATE = date.today().isoformat()
AGENCY = "国家统计局"


def load_registry() -> dict:
    return yaml.safe_load((ROOT / "data" / "registry" / "indicators.yaml").read_text(encoding="utf-8"))


def _status(value) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "未知"
    text = str(value).strip()
    if text in {"", "nan", "None"}:
        return "未知"
    return text


def _base_row(registry_by_id: dict, indicator_id: str) -> dict:
    meta = registry_by_id[indicator_id]
    return {
        "name_zh": meta["name_zh"],
        "name_en": meta["name_en"],
        "definition": meta["definition"],
        "unit": meta["unit"],
    }


def observations_from_workbooks(registry_by_id: dict) -> pd.DataFrame:
    manifest = json.loads((RAW / "manifest.json").read_text(encoding="utf-8"))
    rows: list[dict] = []
    for item in manifest["fetched"]:
        path = ROOT / item["path"]
        if not path.exists():
            continue
        frame = read_workbook(path)
        extracted = extract_frame(frame, item["title"])
        for record in extracted:
            indicator_id = record["indicator_id"]
            if indicator_id not in registry_by_id:
                continue
            meta = _base_row(registry_by_id, indicator_id)
            processing = "读取《中国统计年鉴》Excel原表；不做插值。同一地区同一年保留年鉴版本较新的记录。"
            if indicator_id == "age-65-share":
                processing += " 占比 = 同表65岁及以上人口数 / 同表人口数 × 100。"
            rows.append(
                {
                    **meta,
                    "indicator_id": indicator_id,
                    "region_code": record["region_code"],
                    "region_name": record["region_name"],
                    "year": int(record["year"]),
                    "value": float(record["value"]),
                    "source_agency": AGENCY,
                    "source_url": item["url"],
                    "source_table": f"中国统计年鉴{item['yearbook_year']} {item['title']}",
                    "publish_date": "",
                    "retrieval_date": RETRIEVAL_DATE,
                    "status": "未知",
                    "scope_note": record.get("table_note") or "",
                    "processing": processing,
                    "yearbook_year": int(item["yearbook_year"]),
                    "source_priority": 10,
                    "source_kind": "yearbook_xls",
                }
            )
    return pd.DataFrame(rows)


def observations_from_manual(registry_by_id: dict) -> pd.DataFrame:
    rows: list[dict] = []
    for path in sorted(MANUAL.glob("*.csv")):
        frame = pd.read_csv(path, dtype={"region_code": str})
        for record in frame.to_dict(orient="records"):
            indicator_id = record["indicator_id"]
            meta = _base_row(registry_by_id, indicator_id)
            region = BY_CODE[str(record["region_code"]).zfill(6)]
            rows.append(
                {
                    **meta,
                    "indicator_id": indicator_id,
                    "region_code": region["code"],
                    "region_name": region["name_zh"],
                    "year": int(record["year"]),
                    "value": float(record["value"]),
                    "source_agency": AGENCY,
                    "source_url": record["source_url"],
                    "source_table": record["source_table"],
                    "publish_date": "",
                    "retrieval_date": RETRIEVAL_DATE,
                    "status": _status(record.get("status")),
                    "scope_note": str(record.get("scope_note") or ""),
                    "processing": "人工核对《中国统计年鉴》印本图像后录入，未插值。自动更新不得覆盖 data/manual 中的文件。",
                    "yearbook_year": int(record["yearbook_year"]),
                    "source_priority": 100,
                    "source_kind": "manual_review",
                }
            )
    return pd.DataFrame(rows)


def _population_lookup(raw: pd.DataFrame) -> dict[tuple[str, int], float]:
    subset = raw[raw["indicator_id"] == "population"]
    # Prefer manual, then newer yearbook, so the check uses the same rule as publishing.
    subset = subset.sort_values(["source_priority", "yearbook_year"])
    lookup: dict[tuple[str, int], float] = {}
    for record in subset.itertuples(index=False):
        lookup[(record.region_code, int(record.year))] = float(record.value)
    return lookup


def observations_from_gdp_image(registry_by_id: dict, population: dict[tuple[str, int], float]) -> tuple[pd.DataFrame, list[dict]]:
    path = MANUAL / "gdp_2024_rows.json"
    if not path.exists():
        return pd.DataFrame(), []
    payload = json.loads(path.read_text(encoding="utf-8"))
    report = []
    rows = []
    for item in payload["rows"]:
        code = item["region_code"]
        numbers = item["numbers"]
        gdp = float(numbers[0])
        pop = population.get((code, 2024))
        per_capita = None
        if pop and pop > 0:
            expected = gdp / pop * 10000
            candidates = []
            for number in numbers[1:]:
                if expected <= 0:
                    continue
                gap = abs(float(number) / expected - 1)
                if gap <= 0.03 and float(number) > 5000:
                    candidates.append((gap, float(number)))
            if candidates:
                candidates.sort()
                per_capita = candidates[0][1]
                report.append({"region_code": code, "gdp": gdp, "per_capita": per_capita, "expected_year_end": expected, "gap": candidates[0][0], "status": "accepted"})
            else:
                report.append({"region_code": code, "gdp": gdp, "expected_year_end": expected, "status": "per_capita_rejected"})
        else:
            report.append({"region_code": code, "gdp": gdp, "status": "no_population_for_check"})
        region = BY_CODE[code]
        common = {
            **_base_row(registry_by_id, "gdp"),
            "region_code": code,
            "region_name": region["name_zh"],
            "year": 2024,
            "source_agency": AGENCY,
            "source_url": payload["source_url"],
            "source_table": payload["source_table"],
            "publish_date": "",
            "retrieval_date": RETRIEVAL_DATE,
            "status": "未知",
            "scope_note": payload.get("scope_note") or "",
            "yearbook_year": 2025,
            "source_priority": 100,
            "source_kind": "manual_review",
        }
        rows.append({**common, "indicator_id": "gdp", "value": gdp, "processing": "人工核对年鉴2025表3-9图像的地区生产总值列，未插值。自动流程不覆盖该转录。"})
        if per_capita is not None:
            per_meta = _base_row(registry_by_id, "gdp-per-capita")
            rows.append(
                {
                    **common,
                    **per_meta,
                    "indicator_id": "gdp-per-capita",
                    "value": per_capita,
                    "processing": "人工核对年鉴2025表3-9的人均地区生产总值列，未插值；仅当该数与「现价GDP / 年末常住人口」相差不超过3%时入库。官方人均使用平均人口，故不要求完全相等，也不用年末人口自行代替官方数。",
                }
            )
    return pd.DataFrame(rows), report


def dedupe(raw: pd.DataFrame) -> pd.DataFrame:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    database = PROCESSED / "atlas.duckdb"
    if database.exists():
        database.unlink()
    connection = duckdb.connect(str(database))
    connection.register("raw_df", raw)
    connection.execute("CREATE TABLE raw AS SELECT * FROM raw_df")
    connection.execute(
        """
        CREATE TABLE published AS
        SELECT * EXCLUDE (rn) FROM (
            SELECT *,
                   row_number() OVER (
                       PARTITION BY indicator_id, region_code, year
                       ORDER BY source_priority DESC, yearbook_year DESC, source_url
                   ) AS rn
            FROM raw
            WHERE value IS NOT NULL
        )
        WHERE rn = 1
        """
    )
    published = connection.execute("SELECT * FROM published").fetchdf()
    vintages = connection.execute(
        """
        SELECT indicator_id, region_code, year, count(*) AS n_vintages,
               max(value) AS max_value, min(value) AS min_value
        FROM raw
        GROUP BY 1, 2, 3
        HAVING count(*) > 1
        """
    ).fetchdf()
    connection.close()
    published.attrs["vintages"] = vintages
    return published


def _break_years(meta: dict) -> set[int]:
    return {int(item["year"]) for item in meta.get("breaks") or []}


def add_comparability(published: pd.DataFrame, registry_by_id: dict, vintages: pd.DataFrame | None = None) -> pd.DataFrame:
    frame = published.copy()
    frame["revision_flag"] = False
    if vintages is None:
        vintages = pd.DataFrame()
    revised_keys = set()
    if not vintages.empty:
        for record in vintages.itertuples(index=False):
            span = abs(float(record.max_value) - float(record.min_value))
            base = abs(float(record.max_value)) or 1
            meta = registry_by_id[record.indicator_id]
            if meta.get("yoy_method") == "diff":
                changed = span >= 0.05
            else:
                changed = span / base >= 0.005
            if changed:
                revised_keys.add((record.indicator_id, record.region_code, int(record.year)))
    frame["revision_flag"] = [
        (row.indicator_id, row.region_code, int(row.year)) in revised_keys for row in frame.itertuples(index=False)
    ]
    frame = frame.sort_values(["indicator_id", "region_code", "year"])
    yoy_values = []
    comparable_flags = []
    previous_cache: dict[tuple[str, str], tuple[int, float, int, str]] = {}
    # Iterate in order; build previous as we go, but we need previous year specifically.
    grouped_prev: dict[tuple[str, str, int], tuple] = {}
    for row in frame.itertuples(index=False):
        grouped_prev[(row.indicator_id, row.region_code, int(row.year))] = row

    for row in frame.itertuples(index=False):
        meta = registry_by_id[row.indicator_id]
        method = meta.get("yoy_method")
        previous = grouped_prev.get((row.indicator_id, row.region_code, int(row.year) - 1))
        comparable = False
        yoy = None
        if previous is not None and method in {"pct", "diff"}:
            same_book = int(previous.yearbook_year) == int(row.yearbook_year)
            break_year = int(row.year) in _break_years(meta)
            scope_shift = ("抽样" in str(previous.scope_note)) != ("抽样" in str(row.scope_note)) and (
                "抽样" in str(previous.scope_note) or "抽样" in str(row.scope_note)
            )
            if same_book and not break_year and not scope_shift and previous.value not in (0, None):
                comparable = True
                if method == "pct":
                    yoy = (float(row.value) / float(previous.value) - 1) * 100
                else:
                    yoy = float(row.value) - float(previous.value)
        yoy_values.append(yoy)
        comparable_flags.append(comparable)
        previous_cache[(row.indicator_id, row.region_code)] = (int(row.year), float(row.value), int(row.yearbook_year), str(row.scope_note))
    frame["yoy"] = yoy_values
    frame["yoy_comparable"] = comparable_flags
    # Population before the resident-population break carries an explicit scope sentence.
    notes = []
    for row in frame.itertuples(index=False):
        note = str(row.scope_note or "")
        if row.indicator_id == "population" and int(row.year) < 2005:
            extra = "分地区口径：所引年鉴脚注写明2005年起才是常住人口，本年不应与2005年及以后直接同比。"
            note = (note + " " + extra).strip()
        notes.append(note)
    frame["scope_note"] = notes
    return frame


def _latest(frame: pd.DataFrame, indicator_id: str, region_code: str | None = None) -> pd.Series | None:
    subset = frame[frame["indicator_id"] == indicator_id]
    if region_code:
        subset = subset[subset["region_code"] == region_code]
    else:
        subset = subset[subset["region_code"] != "000000"]
    if subset.empty:
        return None
    year = int(subset["year"].max())
    latest = subset[subset["year"] == year]
    return latest


def build_findings(frame: pd.DataFrame) -> list[dict]:
    findings = []
    per_capita = frame[(frame.indicator_id == "gdp-per-capita") & (frame.region_code != "000000")]
    if not per_capita.empty:
        year = int(per_capita.year.max())
        current = per_capita[per_capita.year == year]
        if len(current) >= 20:
            top = current.loc[current.value.idxmax()]
            bottom = current.loc[current.value.idxmin()]
            findings.append(
                {
                    "indicator_id": "gdp-per-capita",
                    "year": year,
                    "text": (
                        f"{year}年，已入库的{len(current)}个省级地区里，人均地区生产总值（现价）最高的是"
                        f"{top.region_name}（{top.value:,.0f}元），最低的是{bottom.region_name}（{bottom.value:,.0f}元）。"
                        "这是同一指标的水平并列，不是对发展原因的判断。"
                    ),
                }
            )
    population = frame[(frame.indicator_id == "population") & (frame.region_code != "000000")]
    if not population.empty and {2020, 2024}.issubset(set(population.year.unique())):
        wide = population[population.year.isin([2020, 2024])].pivot_table(index="region_code", columns="year", values="value")
        if 2020 in wide.columns and 2024 in wide.columns:
            changed = wide.dropna()
            declined = changed[changed[2024] < changed[2020]].copy()
            declined["delta"] = declined[2024] - declined[2020]
            if not declined.empty:
                worst_code = declined["delta"].idxmin()
                worst = BY_CODE[worst_code]
                findings.append(
                    {
                        "indicator_id": "population",
                        "year": 2024,
                        "text": (
                            f"对比已入库的2020年与2024年年末人口，有{len(declined)}个省级地区的人数下降。"
                            f"减少最多的是{worst['name_zh']}（{declined.loc[worst_code, 2020]:.0f}万 → {declined.loc[worst_code, 2024]:.0f}万）。"
                            "两年都来自年鉴人口表，中间未插值。"
                        ),
                    }
                )
    income = frame[(frame.indicator_id == "disposable-income") & (frame.region_code == "000000")]
    if not income.empty:
        latest = income.sort_values("year").iloc[-1]
        findings.append(
            {
                "indicator_id": "disposable-income",
                "year": int(latest.year),
                "text": (
                    f"{int(latest.year)}年全国居民人均可支配收入为{latest.value:,.0f}元"
                    "（全体居民一体化口径，不与2013年调查改革前的城镇或农村收入拼接）。"
                ),
            }
        )
    urban = frame[(frame.indicator_id == "urbanization") & (frame.region_code == "000000")]
    if not urban.empty:
        latest = urban.sort_values("year").iloc[-1]
        provinces = frame[(frame.indicator_id == "urbanization") & (frame.region_code != "000000") & (frame.year == int(latest.year))]
        if not provinces.empty:
            top = provinces.loc[provinces.value.idxmax()]
            findings.append(
                {
                    "indicator_id": "urbanization",
                    "year": int(latest.year),
                    "text": (
                        f"{int(latest.year)}年全国城镇人口比重为{latest.value:.2f}%。"
                        f"同年分省表中最高的是{top.region_name}（{top.value:.2f}%）。"
                    ),
                }
            )
    return findings


def _records(frame: pd.DataFrame) -> list[dict]:
    columns = [
        "year",
        "value",
        "yoy",
        "yoy_comparable",
        "yearbook_year",
        "source_url",
        "source_table",
        "scope_note",
        "status",
        "processing",
        "source_kind",
        "revision_flag",
        "publish_date",
        "retrieval_date",
        "source_agency",
    ]
    records = []
    for row in frame.sort_values("year").itertuples(index=False):
        item = {}
        for column in columns:
            value = getattr(row, column)
            if pd.isna(value):
                value = None
            elif hasattr(value, "item"):
                value = value.item()
            item[column] = value
        item["year"] = int(item["year"])
        item["yearbook_year"] = int(item["yearbook_year"])
        item["yoy_comparable"] = bool(item["yoy_comparable"])
        item["revision_flag"] = bool(item["revision_flag"])
        records.append(item)
    return records


def export_site(frame: pd.DataFrame, registry: dict, findings: list[dict], gdp_report: list[dict]) -> None:
    WEB_DATA.mkdir(parents=True, exist_ok=True)
    (WEB_DATA / "indicators").mkdir(parents=True, exist_ok=True)
    PUBLIC_DL.mkdir(parents=True, exist_ok=True)
    by_id = {item["id"]: item for item in registry["indicators"]}
    cards = []
    for meta in registry["indicators"]:
        subset = frame[frame.indicator_id == meta["id"]]
        national = subset[subset.region_code == "000000"].sort_values("year")
        provincial = subset[subset.region_code != "000000"]
        latest_year = int(subset.year.max()) if not subset.empty else None
        latest_national = None
        if not national.empty:
            last = national.iloc[-1]
            latest_national = {"year": int(last.year), "value": float(last.value)}
        series = {}
        for code, group in subset.groupby("region_code"):
            series[code] = _records(group)
        sources = (
            subset.groupby(["yearbook_year", "source_table", "source_url"], dropna=False)
            .size()
            .reset_index(name="n")
            .sort_values("yearbook_year")
        )
        payload = {
            "meta": meta,
            "sources": sources.to_dict(orient="records"),
            "series": series,
            "year_min": int(subset.year.min()) if not subset.empty else None,
            "year_max": latest_year,
            "n_obs": int(len(subset)),
            "n_provinces": int(provincial.region_code.nunique()) if not provincial.empty else 0,
        }
        (WEB_DATA / "indicators" / f"{meta['id']}.json").write_text(
            json.dumps(payload, ensure_ascii=False),
            encoding="utf-8",
        )
        subset.to_csv(PUBLIC_DL / f"{meta['id']}.csv", index=False)
        latest_slice = None
        if not provincial.empty:
            slice_year = int(provincial["year"].max())
            current = provincial[provincial["year"] == slice_year]
            latest_slice = {
                "year": slice_year,
                "values": {str(row.region_code): float(row.value) for row in current.itertuples(index=False)},
            }
        cards.append(
            {
                "id": meta["id"],
                "slug": meta["slug"],
                "category": meta["category"],
                "name_zh": meta["name_zh"],
                "name_en": meta["name_en"],
                "unit": meta["unit"],
                "decimals": meta.get("decimals", 0),
                "definition": meta["definition"],
                "geography": meta.get("geography", "provincial"),
                "geography_note": meta.get("geography_note", ""),
                "series_start_note": meta.get("series_start_note", ""),
                "year_min": payload["year_min"],
                "year_max": payload["year_max"],
                "n_obs": payload["n_obs"],
                "n_provinces": payload["n_provinces"],
                "latest_national": latest_national,
                "latest_slice": latest_slice,
                "related": meta.get("related", []),
                "yoy_label_zh": meta.get("yoy_label_zh", ""),
                "national_benchmark_line": meta.get("national_benchmark_line", False),
                "additive": meta.get("additive", False),
            }
        )
    regions_payload = {
        "national": NATIONAL,
        "provinces": REGIONS,
        "macro_regions": MACRO_REGIONS,
        "nbs_regions": NBS_REGIONS,
        "coverage_note": "统计范围是中国大陆31个省级地区。香港、澳门、台湾不在本产品的数据覆盖内；缺数不是关于领土的表述。",
    }
    summary = {
        "generated_on": RETRIEVAL_DATE,
        "categories": registry["categories"],
        "indicators": cards,
        "findings": findings,
        "regions": regions_payload,
        "stats": {
            "indicator_count": len(cards),
            "observation_count": int(len(frame)),
            "province_count": 31,
            "source_agency": AGENCY,
        },
        "gdp_2024_transcription_check": gdp_report,
    }
    (WEB_DATA / "summary.json").write_text(json.dumps(summary, ensure_ascii=False), encoding="utf-8")
    (ROOT / "data" / "regions.json").write_text(json.dumps(regions_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    frame.to_csv(PROCESSED / "observations.csv", index=False)
    frame.to_csv(PUBLIC_DL / "all-observations.csv", index=False)
    export_frame = frame.copy()
    export_frame.attrs = {}
    export_frame.to_parquet(PROCESSED / "observations.parquet", index=False)


def _write_manual_transcriptions() -> None:
    script = ROOT / "data" / "manual" / "transcribe_2025.py"
    spec = importlib.util.spec_from_file_location("transcribe_2025", script)
    if spec is None or spec.loader is None:
        raise RuntimeError("manual transcription script is missing")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.main()
    gap = ROOT / "data" / "manual" / "gdp_gap.py"
    gap_spec = importlib.util.spec_from_file_location("gdp_gap", gap)
    if gap_spec is None or gap_spec.loader is None:
        raise RuntimeError("gdp gap script is missing")
    gap_module = importlib.util.module_from_spec(gap_spec)
    gap_spec.loader.exec_module(gap_module)
    gap_module.main()


def build() -> pd.DataFrame:
    _write_manual_transcriptions()
    registry = load_registry()
    registry_by_id = {item["id"]: item for item in registry["indicators"]}
    workbook = observations_from_workbooks(registry_by_id)
    manual = observations_from_manual(registry_by_id)
    parts = [part for part in (workbook, manual) if not part.empty]
    raw = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()
    gdp_rows, gdp_report = observations_from_gdp_image(registry_by_id, _population_lookup(raw))
    if not gdp_rows.empty:
        raw = pd.concat([raw, gdp_rows], ignore_index=True)
    (PROCESSED).mkdir(parents=True, exist_ok=True)
    (PROCESSED / "gdp_2024_check.json").write_text(json.dumps(gdp_report, ensure_ascii=False, indent=2), encoding="utf-8")
    raw.to_csv(PROCESSED / "observations_all_vintages.csv", index=False)
    published = dedupe(raw)
    published["region_code"] = published["region_code"].astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(6)
    vintages = published.attrs.get("vintages")
    if isinstance(vintages, pd.DataFrame) and not vintages.empty:
        vintages = vintages.copy()
        vintages["region_code"] = vintages["region_code"].astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(6)
    published = add_comparability(published, registry_by_id, vintages if isinstance(vintages, pd.DataFrame) else pd.DataFrame())
    if isinstance(vintages, pd.DataFrame):
        published.attrs["vintages"] = vintages
        vintages.to_csv(PROCESSED / "vintage_conflicts.csv", index=False)
    findings = build_findings(published)
    export_site(published, registry, findings, gdp_report)
    write_docs(published, registry)
    return published


def write_docs(frame: pd.DataFrame, registry: dict) -> None:
    dictionary = ["# 数据字典", "", "机器可读的定义在 `data/registry/indicators.yaml`。下表是发布库中的指标。", ""]
    dictionary.append("| 指标 | 中文名 | 单位 | 年份 | 观测数 | 省级地区数 |")
    dictionary.append("| --- | --- | --- | --- | --- | --- |")
    for meta in registry["indicators"]:
        subset = frame[frame["indicator_id"] == meta["id"]]
        provinces = subset[subset["region_code"] != "000000"]["region_code"].nunique()
        span = "—" if subset.empty else f"{int(subset.year.min())}–{int(subset.year.max())}"
        dictionary.append(
            f"| `{meta['id']}` | {meta['name_zh']} | {meta['unit']} | {span} | {len(subset)} | {provinces} |"
        )
    dictionary.append("")
    dictionary.append("地区代码使用 GB/T 2260 的省级 6 位码。`000000` 表示年鉴中的全国合计，不是 GB/T 2260 代码。")
    dictionary.append("状态字段当前为「未知」：年鉴表本身通常不标注初步数或最终数。出版日期在表内没有精确到日，故留空，年鉴年份写在来源表名中。")
    (ROOT / "docs" / "data-dictionary.md").write_text("\n".join(dictionary) + "\n", encoding="utf-8")

    inventory = ["# 来源清单", "", "每条观测的网址在 `data/processed/observations.csv` 的 `source_url`。下表是去重后的来源表。", ""]
    inventory.append("| 年鉴年 | 来源表 | 观测数 | 网址 |")
    inventory.append("| --- | --- | --- | --- |")
    grouped = (
        frame.groupby(["yearbook_year", "source_table", "source_url"], dropna=False)
        .size()
        .reset_index(name="n")
        .sort_values(["yearbook_year", "source_table"])
    )
    for record in grouped.itertuples(index=False):
        inventory.append(f"| {int(record.yearbook_year)} | {record.source_table} | {int(record.n)} | {record.source_url} |")
    inventory.append("")
    inventory.append("国家数据 data.stats.gov.cn 在构建环境返回 403 UrlACL，未作为来源。人工录入文件位于 `data/manual/`，优先级高于自动解析，流水线不会覆盖它们。")
    (ROOT / "docs" / "source-inventory.md").write_text("\n".join(inventory) + "\n", encoding="utf-8")
