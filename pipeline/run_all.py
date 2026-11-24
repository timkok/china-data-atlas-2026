"""Run fetch (unless --offline), standardize, and write the site dataset."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from pipeline.build import build
from pipeline.fetch import fetch

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--offline", action="store_true", help="Use committed raw workbooks; do not download")
    parser.add_argument("--skip-fetch", action="store_true")
    args = parser.parse_args()
    manifest = ROOT / "data" / "raw" / "yearbook" / "manifest.json"
    if not args.offline and not args.skip_fetch:
        fetch()
    elif not manifest.exists():
        raise SystemExit("No yearbook manifest. Run without --offline first.")
    published = build()
    counts = published.groupby("indicator_id").size().to_dict()
    summary = {
        "observations": int(len(published)),
        "by_indicator": {key: int(value) for key, value in counts.items()},
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
