"""Download China Statistical Yearbook worksheets that are published as Excel.

data.stats.gov.cn returns 403 UrlACL from this environment. This fetcher uses
only the public yearbook pages on www.stats.gov.cn and does not retry around
access controls. Image-only tables are recorded and left for the manual path.
"""

from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

from pipeline.extract import classify_title

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "yearbook"
CATALOG = ROOT / "data" / "raw" / "catalog"
USER_AGENT = (
    "Mozilla/5.0 (compatible; ChinaDataAtlas/0.1; "
    "+https://github.com/timkok/china-data-atlas-2026) yearbook-table-fetch"
)
BASE = "https://www.stats.gov.cn/sj/ndsj/{year}/"


def _get(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept-Language": "zh-CN,zh;q=0.9"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def _decode(raw: bytes) -> str:
    for encoding in ("gb18030", "gbk", "utf-8"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("gb18030", errors="replace")


def parse_left(html: str) -> list[dict]:
    pairs = re.findall(r"href=['\"]([^'\"]+)['\"][^>]*>([^<]+)", html, flags=re.I)
    tables = []
    for href, title in pairs:
        cleaned = re.sub(r"\s+", "", title)
        href = href.replace("\\", "/").strip()
        if not cleaned or href.startswith("mailto:"):
            continue
        tables.append({"href": href, "title": cleaned})
    return tables


def xls_url(year: int, href: str) -> str | None:
    lower = href.lower()
    if lower.endswith((".jpg", ".jpeg", ".htm", ".html")):
        stem = href.rsplit(".", 1)[0]
        return BASE.format(year=year) + stem + ".xls"
    return None


def fetch(years: range | list[int] | None = None, pause: float = 0.25) -> dict:
    years = list(years or range(2005, 2026))
    RAW.mkdir(parents=True, exist_ok=True)
    CATALOG.mkdir(parents=True, exist_ok=True)
    manifest = {"fetched": [], "image_only": [], "failed": [], "skipped_title": []}
    for year in years:
        left_url = BASE.format(year=year) + "left.htm"
        try:
            html = _decode(_get(left_url))
        except Exception as exc:  # noqa: BLE001 - record and continue
            manifest["failed"].append({"year": year, "url": left_url, "error": str(exc)})
            continue
        tables = parse_left(html)
        (CATALOG / f"{year}.json").write_text(json.dumps(tables, ensure_ascii=False, indent=2), encoding="utf-8")
        time.sleep(pause)
        for table in tables:
            kind = classify_title(table["title"])
            if not kind:
                continue
            url = xls_url(year, table["href"])
            if not url:
                manifest["image_only"].append({"year": year, "title": table["title"], "href": table["href"], "kind": kind})
                continue
            filename = f"{year}__{kind}__{Path(url).name}"
            # Disambiguate identical filenames used by different tables in one year.
            filename = f"{year}__{kind}__{re.sub(r'[^0-9A-Za-z._-]+', '_', table['title'])[:40]}__{Path(url).name}"
            dest = RAW / filename
            record = {
                "yearbook_year": year,
                "kind": kind,
                "title": table["title"],
                "url": url,
                "page": BASE.format(year=year) + table["href"],
                "path": str(dest.relative_to(ROOT)),
            }
            if dest.exists() and dest.stat().st_size > 2000 and dest.read_bytes()[:4] == b"\xd0\xcf\x11\xe0":
                manifest["fetched"].append(record)
                continue
            try:
                payload = _get(url)
            except urllib.error.HTTPError as exc:
                if exc.code == 404:
                    manifest["image_only"].append({**record, "reason": "xls_404"})
                else:
                    manifest["failed"].append({**record, "error": f"HTTP {exc.code}"})
                time.sleep(pause)
                continue
            except Exception as exc:  # noqa: BLE001
                manifest["failed"].append({**record, "error": str(exc)})
                time.sleep(pause)
                continue
            if payload[:4] != b"\xd0\xcf\x11\xe0":
                manifest["failed"].append({**record, "error": "not an OLE workbook"})
                continue
            dest.write_bytes(payload)
            manifest["fetched"].append(record)
            time.sleep(pause)
    (RAW / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        f"workbooks {len(manifest['fetched'])} | image-only {len(manifest['image_only'])} | failed {len(manifest['failed'])}"
    )
    return manifest


if __name__ == "__main__":
    fetch()
