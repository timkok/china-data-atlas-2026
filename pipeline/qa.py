"""Data quality gate.

Structural checks fail the process. Anomalies, missing cells and vintage
conflicts are reported and saved; they do not by themselves mean a figure
was invented. National totals are never required to equal the sum of
provinces unless the indicator is marked additive.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path

import pandas as pd
import yaml

from pipeline.regions import BY_CODE

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
QA_DIR = ROOT / "data" / "qa"


def _load() -> tuple[pd.DataFrame, dict]:
    frame = pd.read_csv(PROCESSED / "observations.csv", dtype={"region_code": str})
    frame["region_code"] = frame["region_code"].str.zfill(6)
    registry = yaml.safe_load((ROOT / "data" / "registry" / "indicators.yaml").read_text(encoding="utf-8"))
    return frame, registry


def _link_checks(urls: list[str]) -> list[dict]:
    if os.environ.get("CDA_SKIP_LINK_CHECK") == "1":
        return [{"url": url, "status": "skipped"} for url in urls]
    results = []
    for url in urls:
        request = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "ChinaDataAtlas-QA/0.1"})
        status = None
        error = ""
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                status = response.status
        except urllib.error.HTTPError as exc:
            status = exc.code
            if exc.code in {403, 405}:
                # Some static files reject HEAD. Confirm with a tiny GET.
                try:
                    get_request = urllib.request.Request(url, headers={"User-Agent": "ChinaDataAtlas-QA/0.1", "Range": "bytes=0-32"})
                    with urllib.request.urlopen(get_request, timeout=30) as response:
                        status = response.status
                except urllib.error.HTTPError as get_exc:
                    status = get_exc.code
                    error = str(get_exc)
                except Exception as get_exc:  # noqa: BLE001
                    error = str(get_exc)
        except Exception as exc:  # noqa: BLE001
            error = str(exc)
        results.append({"url": url, "status": status, "error": error})
    return results


def run_qa() -> dict:
    frame, registry = _load()
    by_id = {item["id"]: item for item in registry["indicators"]}
    failures: list[str] = []
    warnings: list[str] = []

    allowed_codes = set(BY_CODE)
    bad_codes = sorted(set(frame["region_code"]) - allowed_codes)
    if bad_codes:
        failures.append(f"unknown region codes: {bad_codes}")
    if frame["year"].isna().any() or not frame["year"].between(1978, 2030).all():
        failures.append("year out of range or missing")
    if not pd.api.types.is_numeric_dtype(frame["value"]):
        failures.append("value column is not numeric")
    if frame["value"].isna().any():
        failures.append("published table contains null values; missing years should be omitted, not filled")
    duplicate = frame.duplicated(["indicator_id", "region_code", "year"])
    if duplicate.any():
        failures.append(f"duplicate published keys: {int(duplicate.sum())}")
    unknown_indicators = sorted(set(frame["indicator_id"]) - set(by_id))
    if unknown_indicators:
        failures.append(f"indicators missing from registry: {unknown_indicators}")

    for indicator_id, meta in by_id.items():
        subset = frame[frame["indicator_id"] == indicator_id]
        if subset.empty:
            failures.append(f"{indicator_id} has no observations")
            continue
        wrong_unit = subset[subset["unit"] != meta["unit"]]
        if not wrong_unit.empty:
            failures.append(f"{indicator_id} has rows with a unit other than {meta['unit']}")
        if subset["source_url"].fillna("").eq("").any():
            failures.append(f"{indicator_id} has a row without a source URL")
        if subset["source_table"].fillna("").eq("").any():
            failures.append(f"{indicator_id} has a row without a source table")
        if not subset["source_agency"].eq("国家统计局").all():
            failures.append(f"{indicator_id} has a non-NBS source agency")

    # Additivity only where the registry says the indicator is a sum of provinces.
    additivity = []
    for meta in registry["indicators"]:
        if not meta.get("additive"):
            continue
        subset = frame[frame["indicator_id"] == meta["id"]]
        for year, group in subset.groupby("year"):
            national = group[group["region_code"] == "000000"]
            provinces = group[group["region_code"] != "000000"]
            if national.empty or provinces["region_code"].nunique() < 31:
                additivity.append({"indicator_id": meta["id"], "year": int(year), "status": "incomplete"})
                continue
            total = float(provinces["value"].sum())
            published = float(national["value"].iloc[0])
            gap = abs(total - published) / published if published else None
            status = "ok" if gap is not None and gap <= 0.005 else "mismatch"
            additivity.append(
                {"indicator_id": meta["id"], "year": int(year), "province_sum": total, "national": published, "relative_gap": gap, "status": status}
            )
            if status == "mismatch":
                failures.append(f"{meta['id']} {year} provincial sum differs from national by {gap:.2%}")

    anomalies = []
    for meta in registry["indicators"]:
        subset = frame[frame["indicator_id"] == meta["id"]].sort_values(["region_code", "year"])
        rule = meta.get("anomaly") or {}
        for code, group in subset.groupby("region_code"):
            previous = None
            for row in group.itertuples(index=False):
                if previous is not None and int(row.year) == int(previous.year) + 1:
                    if "yoy_abs" in rule and previous.value:
                        change = abs(float(row.value) / float(previous.value) - 1)
                        if change > float(rule["yoy_abs"]):
                            anomalies.append(
                                {"indicator_id": meta["id"], "region_code": code, "year": int(row.year), "kind": "yoy", "change": change}
                            )
                    if "diff_abs" in rule:
                        change = abs(float(row.value) - float(previous.value))
                        if change > float(rule["diff_abs"]):
                            anomalies.append(
                                {"indicator_id": meta["id"], "region_code": code, "year": int(row.year), "kind": "diff", "change": change}
                            )
                    if "jump_from" in rule:
                        change = abs(float(row.value) - float(rule["jump_from"]))
                        if change > float(rule["jump_abs"]):
                            anomalies.append(
                                {"indicator_id": meta["id"], "region_code": code, "year": int(row.year), "kind": "index_jump", "change": change}
                            )
                previous = row

    # Site JSON must show the same values as the published table.
    consistency = []
    web_root = ROOT / "web" / "data" / "indicators"
    for meta in registry["indicators"]:
        path = web_root / f"{meta['id']}.json"
        if not path.exists():
            failures.append(f"missing site json for {meta['id']}")
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        for code, series in payload["series"].items():
            for point in series:
                match = frame[
                    (frame["indicator_id"] == meta["id"])
                    & (frame["region_code"] == str(code).zfill(6))
                    & (frame["year"] == int(point["year"]))
                ]
                if match.empty or abs(float(match.iloc[0]["value"]) - float(point["value"])) > 1e-6:
                    consistency.append({"indicator_id": meta["id"], "region_code": code, "year": point["year"]})
    if consistency:
        failures.append(f"site json disagrees with observations.csv in {len(consistency)} cells")

    # Missing-cell report: within each indicator's observed year span, which province-years are absent.
    missing = []
    for meta in registry["indicators"]:
        subset = frame[(frame["indicator_id"] == meta["id"]) & (frame["region_code"] != "000000")]
        if subset.empty:
            continue
        years = range(int(subset.year.min()), int(subset.year.max()) + 1)
        provinces = [code for code in BY_CODE if code != "000000"]
        present = set(zip(subset["region_code"], subset["year"].astype(int)))
        absent = [(code, year) for code in provinces for year in years if (code, year) not in present]
        missing.append(
            {
                "indicator_id": meta["id"],
                "year_min": int(subset.year.min()),
                "year_max": int(subset.year.max()),
                "present": int(len(present)),
                "absent_inside_span": len(absent),
                "geography": meta.get("geography", "provincial"),
            }
        )

    urls = sorted(set(frame["source_url"].dropna()))
    links = _link_checks(urls)
    broken = [item for item in links if item.get("status") not in (200, 206, "skipped") and not str(item.get("status", "")).startswith("2")]
    # 206 is partial content from Range requests. Treat 200-class as ok.
    broken = [item for item in links if isinstance(item.get("status"), int) and not (200 <= item["status"] < 300)]
    if broken and os.environ.get("CDA_SKIP_LINK_CHECK") != "1":
        failures.append(f"{len(broken)} source URLs did not return a success status")

    scope_flags = []
    for meta in registry["indicators"]:
        for item in meta.get("breaks") or []:
            scope_flags.append({"indicator_id": meta["id"], "year": item["year"], "note": item["note"]})

    report = {
        "ok": not failures,
        "failures": failures,
        "warnings": warnings,
        "n_observations": int(len(frame)),
        "n_indicators": int(frame["indicator_id"].nunique()),
        "anomalies": anomalies,
        "additivity": additivity,
        "missing": missing,
        "links": links,
        "consistency_mismatches": consistency[:20],
        "scope_break_flags": scope_flags,
    }
    QA_DIR.mkdir(parents=True, exist_ok=True)
    (QA_DIR / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    result = run_qa()
    print(json.dumps({"ok": result["ok"], "failures": result["failures"], "n": result["n_observations"], "anomalies": len(result["anomalies"])}, ensure_ascii=False, indent=2))
    if not result["ok"]:
        raise SystemExit(1)
