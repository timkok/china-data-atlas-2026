"""Turn China Statistical Yearbook worksheets into long observations.

The parser is driven by the table title. New tables of a known shape can be
added by extending TITLE_RULES; the website does not need a new template.
"""

from __future__ import annotations

import math
import re
from typing import Any

import pandas as pd

from pipeline.regions import match_region

YEAR_MIN = 1978
YEAR_MAX = 2030


def clean_text(value: Any) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ""
    text = str(value).replace("\u3000", "").replace("\xa0", "")
    text = re.sub(r"\s+", "", text)
    return text.strip()


def as_year(value: Any) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)) and not (isinstance(value, float) and math.isnan(value)):
        if float(value) == int(value) and YEAR_MIN <= int(value) <= YEAR_MAX:
            return int(value)
        return None
    text = clean_text(value)
    matched = re.fullmatch(r"(19|20)\d{2}", text)
    if matched and YEAR_MIN <= int(text) <= YEAR_MAX:
        return int(text)
    return None


def title_year(title: str) -> int | None:
    matched = re.search(r"(20\d{2}|19\d{2})\s*年", title)
    if matched:
        return int(matched.group(1))
    return None


def to_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        if isinstance(value, float) and math.isnan(value):
            return None
        return float(value)
    text = str(value).strip().replace(",", "").replace("，", "")
    if text in {"", "-", "—", "–", "…", "...", ".", "nan", "None"}:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def footnotes(df: pd.DataFrame) -> str:
    notes: list[str] = []
    for value in df.to_numpy().ravel():
        text = str(value) if value is not None and not (isinstance(value, float) and math.isnan(value)) else ""
        compact = text.strip()
        if compact.startswith("注"):
            notes.append(re.sub(r"\s+", " ", compact))
    # Preserve order and drop duplicates.
    seen: set[str] = set()
    unique = []
    for note in notes:
        if note not in seen:
            seen.add(note)
            unique.append(note)
    return " ".join(unique)[:800]


def header_limit(df: pd.DataFrame, default: int = 12) -> int:
    """Rows before the first provincial or national label are headers, not data."""
    for index in range(len(df)):
        if match_region(df.iat[index, 0]):
            return index
        # National time-series tables put a year in column 0. Stop before the first one
        # once a header row has already been seen.
        if index > 2 and as_year(df.iat[index, 0]):
            return index
    return min(default, len(df))


def column_contexts(df: pd.DataFrame, scan_rows: int | None = None) -> list[dict]:
    """Label and year associated with each column, inheriting merged headers."""
    contexts: list[dict] = []
    nrows = header_limit(df) if scan_rows is None else min(scan_rows, len(df))
    for col in range(df.shape[1]):
        labels: list[str] = []
        year = None
        for row in range(nrows):
            value = df.iat[row, col]
            found = as_year(value)
            if found:
                year = found
                continue
            text = clean_text(value)
            if text and text not in {"地区", "年份", "年", "单位"}:
                labels.append(text)
        contexts.append({"year": year, "labels": labels, "text": "".join(labels)})

    inherited: list[str] = []
    for ctx in contexts:
        if ctx["labels"]:
            inherited = ctx["labels"]
        elif ctx["year"] and inherited:
            ctx["labels"] = list(inherited)
            ctx["text"] = "".join(ctx["labels"])
    return contexts


def iter_region_rows(df: pd.DataFrame):
    for row_index in range(len(df)):
        region = match_region(df.iat[row_index, 0])
        if region:
            yield row_index, region


def iter_year_rows(df: pd.DataFrame):
    for row_index in range(len(df)):
        year = as_year(df.iat[row_index, 0])
        if year and match_region(df.iat[row_index, 0]) is None:
            yield row_index, year


def _emit(rows: list[dict], *, indicator_id: str, region: dict, year: int, value: float, note: str) -> None:
    if year < YEAR_MIN or year > YEAR_MAX:
        return
    if value is None or (isinstance(value, float) and (math.isnan(value) or math.isinf(value))):
        return
    rows.append(
        {
            "indicator_id": indicator_id,
            "region_code": region["code"],
            "region_name": region["name_zh"],
            "year": int(year),
            "value": float(value),
            "table_note": note,
        }
    )


def extract_grid(df: pd.DataFrame, indicator_id: str, note: str, fallback_year: int | None) -> list[dict]:
    contexts = column_contexts(df)
    distinct_years = {ctx["year"] for ctx in contexts if ctx["year"]}
    use_title_year = len(distinct_years) < 2
    rows: list[dict] = []
    for row_index, region in iter_region_rows(df):
        for col, ctx in enumerate(contexts):
            if col == 0:
                continue
            label = ctx["text"]
            if any(token in label for token in ("指数", "增长", "增速")):
                continue
            year = ctx["year"] or (fallback_year if use_title_year else None)
            if not year:
                continue
            value = to_float(df.iat[row_index, col])
            if value is None:
                continue
            _emit(rows, indicator_id=indicator_id, region=region, year=year, value=value, note=note)
    return rows


def extract_gdp(df: pd.DataFrame, note: str, fallback_year: int | None) -> list[dict]:
    contexts = column_contexts(df)
    distinct_years = {ctx["year"] for ctx in contexts if ctx["year"]}
    use_title_year = len(distinct_years) < 2
    rows: list[dict] = []
    for row_index, region in iter_region_rows(df):
        for col, ctx in enumerate(contexts):
            if col == 0:
                continue
            label = ctx["text"]
            year = ctx["year"] or (fallback_year if use_title_year else None)
            if not year:
                continue
            value = to_float(df.iat[row_index, col])
            if value is None:
                continue
            indicator_id = None
            if "人均" in label and "地区生产" in label and "指数" not in label and "构成" not in label:
                indicator_id = "gdp-per-capita"
            elif "指数" in label and "上年" in label and "人均" not in label and not any(
                token in label for token in ("第一", "第二", "第三")
            ):
                indicator_id = "gdp-index"
            elif (
                "地区生产" in label
                and "人均" not in label
                and "指数" not in label
                and "构成" not in label
                and not any(token in label for token in ("第一", "第二", "第三", "农林", "工业", "建筑", "批发", "交通", "住宿", "金融", "房地产", "其他"))
            ):
                indicator_id = "gdp"
            if indicator_id:
                _emit(rows, indicator_id=indicator_id, region=region, year=year, value=value, note=note)
    return rows


def extract_column_match(
    df: pd.DataFrame,
    indicator_id: str,
    note: str,
    fallback_year: int | None,
    predicate,
) -> list[dict]:
    contexts = column_contexts(df)
    columns = [index for index, ctx in enumerate(contexts) if index > 0 and predicate(ctx["text"])]
    rows: list[dict] = []
    for row_index, region in iter_region_rows(df):
        for col in columns:
            year = contexts[col]["year"] or fallback_year
            if not year:
                continue
            value = to_float(df.iat[row_index, col])
            if value is None:
                continue
            _emit(rows, indicator_id=indicator_id, region=region, year=year, value=value, note=note)
    return rows


def extract_national_year_column(df: pd.DataFrame, indicator_id: str, note: str, predicate) -> list[dict]:
    contexts = column_contexts(df)
    columns = [index for index, ctx in enumerate(contexts) if index > 0 and predicate(ctx["text"])]
    national = match_region("全国")
    rows: list[dict] = []
    assert national is not None
    for row_index, year in iter_year_rows(df):
        for col in columns:
            value = to_float(df.iat[row_index, col])
            if value is None:
                continue
            _emit(rows, indicator_id=indicator_id, region=national, year=year, value=value, note=note)
            break
    return rows


def extract_age_share(df: pd.DataFrame, note: str, fallback_year: int | None) -> list[dict]:
    def is_total(text: str) -> bool:
        return "人口数" in text and "岁" not in text and "抚养" not in text

    def is_old(text: str) -> bool:
        return "65岁及以上" in text or "65岁及以上" in text.replace("＋", "+")

    contexts = column_contexts(df)
    total_cols = [i for i, ctx in enumerate(contexts) if i > 0 and is_total(ctx["text"])]
    old_cols = [i for i, ctx in enumerate(contexts) if i > 0 and "65岁" in ctx["text"] and "抚养" not in ctx["text"]]
    if not total_cols or not old_cols:
        return []
    total_col = total_cols[0]
    old_col = old_cols[0]
    year = contexts[total_col]["year"] or contexts[old_col]["year"] or fallback_year
    if not year:
        return []
    rows: list[dict] = []
    for row_index, region in iter_region_rows(df):
        total = to_float(df.iat[row_index, total_col])
        old = to_float(df.iat[row_index, old_col])
        if total is None or old is None or total <= 0:
            continue
        # Both columns are counts in the yearbook (persons, often a sample).
        if old > total:
            continue
        share = old / total * 100
        scope = note
        if "抽样" in note:
            scope = (note + " 占比由同表抽样人数计算。").strip()
        elif year in {2000, 2010, 2020} or "普查" in note:
            scope = (note + " 占比由同表人口数计算。").strip()
        else:
            scope = (note + " 占比由同表人口数计算，不跨表。").strip()
        _emit(rows, indicator_id="age-65-share", region=region, year=year, value=share, note=scope)
    return rows


def extract_higher_ed(df: pd.DataFrame, note: str, fallback_year: int | None) -> list[dict]:
    contexts = column_contexts(df)
    student_cols = []
    school_cols = []
    for index, ctx in enumerate(contexts):
        if index == 0:
            continue
        text = ctx["text"]
        if "学校数" in text and "在校" not in text:
            school_cols.append(index)
        if "在校" in text and "学生" in text and "本科" not in text and "专科" not in text:
            student_cols.append(index)
    rows: list[dict] = []
    for row_index, region in iter_region_rows(df):
        if student_cols:
            value = to_float(df.iat[row_index, student_cols[0]])
            year = contexts[student_cols[0]]["year"] or fallback_year
            if value is not None and year:
                _emit(rows, indicator_id="he-students", region=region, year=year, value=value, note=note)
        if school_cols:
            value = to_float(df.iat[row_index, school_cols[0]])
            year = contexts[school_cols[0]]["year"] or fallback_year
            if value is not None and year:
                _emit(rows, indicator_id="he-schools", region=region, year=year, value=value, note=note)
    return rows


def extract_retail(df: pd.DataFrame, note: str, fallback_year: int | None) -> list[dict]:
    contexts = column_contexts(df)
    rows: list[dict] = []
    for row_index, region in iter_region_rows(df):
        for col, ctx in enumerate(contexts):
            if col == 0:
                continue
            label = ctx["text"]
            if "社会消费品零售总额" not in label:
                continue
            if any(token in label for token in ("增长", "增速", "%")) and "亿元" not in label and "绝对" not in label:
                # Growth columns are labeled 增长 or %. Level columns carry 亿元 or the indicator name alone.
                if "亿元" not in label:
                    continue
            year = ctx["year"] or fallback_year
            if not year:
                continue
            value = to_float(df.iat[row_index, col])
            if value is None:
                continue
            _emit(rows, indicator_id="retail-sales", region=region, year=year, value=value, note=note)
    return rows


def classify_title(title: str) -> str | None:
    text = clean_text(title)
    if not text:
        return None
    if any(token in text for token in ("香港", "澳门", "台湾")) and "分地区" not in text and "各地区" not in text:
        return None
    vocational = "职业" in text
    if ("本专科学生" in text or "学校和学生" in text or "普通高等学校(机构)情况" in text or "普通高等学校情况" in text) and not vocational and "教职工" not in text and "科技" not in text and "分学科" not in text:
        if any(token in text for token in ("分地区", "各地区", "高等学校")):
            return "higher_ed"
    if "附录" in text or "香港" in text or "澳门" in text or "台湾" in text:
        return None
    if "人均地区生产总值" in text:
        return "pcgdp"
    if "人均国内生产总值" in text:
        return None
    if text.find("国内生产总值") != -1 and "地区" not in text and not any(token in text for token in ("指数", "构成", "不变价", "支出")):
        return "national_gdp"
    if "地区生产总值" in text and not any(token in text for token in ("支出法", "收入法", "项目结构", "三次产业", "构成项目")):
        return "gdp"
    if "城镇人口比重" in text:
        return "urban"
    if "年末人口" in text:
        return "population"
    if "出生率" in text and any(token in text for token in ("分地区", "各地区")):
        return "birth_province"
    if "出生率" in text and "死亡" in text and "分地区" not in text and "各地区" not in text:
        return "birth_national"
    if "年龄构成" in text and any(token in text for token in ("分地区", "各地区")):
        return "age"
    if "居民人均可支配收入" in text and not any(token in text for token in ("来源", "城镇", "农村", "五等", "东部", "中、西", "脱贫")):
        return "income"
    if "社会消费品零售总额" in text and "网上" not in text and "限额" not in text:
        return "retail"
    if "每千人口卫生技术" in text:
        return "physicians"
    if "每千人口医疗卫生机构床位" in text and any(token in text for token in ("各地区", "分地区")):
        return "beds_province"
    if "每千人口医疗卫生机构床位" in text:
        return "beds_national"
    return None


def _first_wins(rows: list[dict]) -> list[dict]:
    """Leftmost column is emitted first. Keep that cell if a table matched twice."""
    chosen: dict[tuple, dict] = {}
    for row in rows:
        key = (row["indicator_id"], row["region_code"], row["year"])
        if key not in chosen:
            chosen[key] = row
    return list(chosen.values())


def extract_frame(df: pd.DataFrame, title: str) -> list[dict]:
    kind = classify_title(title)
    if not kind:
        return []
    note = footnotes(df)
    fallback = title_year(title)
    rows: list[dict] = []
    if kind == "population":
        rows = extract_grid(df, "population", note, fallback)
    elif kind == "urban":
        rows = extract_grid(df, "urbanization", note, fallback)
    elif kind == "income":
        rows = extract_grid(df, "disposable-income", note, fallback)
    elif kind == "pcgdp":
        rows = extract_grid(df, "gdp-per-capita", note, fallback)
    elif kind == "gdp":
        rows = extract_gdp(df, note, fallback)
    elif kind == "national_gdp":
        rows = extract_national_year_column(
            df,
            "gdp",
            note,
            lambda text: "国内生产总值" in text and "人均" not in text and "指数" not in text,
        ) or extract_grid(df, "gdp", note, fallback)
    elif kind == "birth_province":
        rows = extract_column_match(
            df,
            "birth-rate",
            note,
            fallback,
            lambda text: "出生率" in text and "死亡" not in text,
        )
    elif kind == "birth_national":
        rows = extract_national_year_column(
            df,
            "birth-rate",
            note,
            lambda text: "出生率" in text and "死亡" not in text,
        )
    elif kind == "age":
        rows = extract_age_share(df, note, fallback)
    elif kind == "retail":
        rows = extract_retail(df, note, fallback)
    elif kind == "higher_ed":
        rows = extract_higher_ed(df, note, fallback)
    elif kind == "physicians":
        rows = extract_national_year_column(
            df,
            "physicians-per-1000",
            note,
            lambda text: "执业" in text and "助理" in text and "合计" in text and "城市" not in text and "农村" not in text,
        )
    elif kind == "beds_province":
        rows = extract_column_match(
            df,
            "beds-per-1000",
            note,
            fallback,
            lambda text: "每千人口" in text and "机构床位" in text and "医院" not in text,
        )
    elif kind == "beds_national":
        rows = extract_national_year_column(
            df,
            "beds-per-1000",
            note,
            lambda text: "每千人口" in text and "床" in text and "合计" in text and "医院" not in text,
        )
    return _first_wins(rows)


def read_workbook(path: str) -> pd.DataFrame:
    return pd.read_excel(path, header=None, engine="xlrd")
