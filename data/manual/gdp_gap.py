"""GDP levels transcribed from yearbook images for years without an Excel file.

A single-year row is kept only when the first number equals the sum of the
next three (the three industries) within 0.8%. That rejects a shifted column.
2014 and 2015 come from the multi-year 2016 yearbook table, whose 2011–2012
columns match the Excel edition, so they are not industry-sum checked.
"""

from __future__ import annotations

import csv
from pathlib import Path

OUT = Path(__file__).resolve().parent
CODES = [
    "110000", "120000", "130000", "140000", "150000",
    "210000", "220000", "230000",
    "310000", "320000", "330000", "340000", "350000", "360000", "370000",
    "410000", "420000", "430000", "440000", "450000", "460000",
    "500000", "510000", "520000", "530000", "540000",
    "610000", "620000", "630000", "640000", "650000",
]

# Four numbers: GRP, primary, secondary, tertiary. 2014/2015 store only GRP.
ROWS: dict[int, list[tuple]] = {
    2014: [(v,) for v in [
        21330.83, 15726.93, 29421.15, 12761.49, 17770.19, 28626.58, 13803.14, 15039.38,
        23567.70, 65088.32, 40173.03, 20848.75, 24055.76, 15714.63, 59426.59,
        34938.24, 27379.22, 27037.32, 67809.85, 15672.89, 3500.72,
        14262.60, 28536.66, 9266.39, 12814.59, 920.83,
        17689.94, 6836.82, 2303.32, 2752.10, 9273.46,
    ]],
    2015: [(v,) for v in [
        23014.59, 16538.19, 29806.11, 12766.49, 17831.51, 28669.02, 14063.13, 15083.67,
        25123.45, 70116.38, 42886.49, 22005.63, 25979.82, 16723.78, 63002.33,
        37002.16, 29550.19, 28902.21, 72812.55, 16803.12, 3702.76,
        15717.27, 30053.10, 10502.56, 13619.17, 1026.39,
        18021.86, 6790.32, 2417.05, 2911.77, 9324.80,
    ]],
    2018: [
        (30319.98, 118.69, 5647.65, 24553.64), (18809.64, 172.71, 7609.81, 11027.12),
        (36010.27, 3338.00, 16040.06, 16632.21), (16818.11, 740.64, 7089.19, 8988.28),
        (17289.22, 1753.82, 6807.30, 8728.10), (25315.35, 2033.30, 10025.10, 13256.95),
        (15074.62, 1160.75, 6410.85, 7503.02), (16361.62, 3000.96, 4030.94, 9329.72),
        (32679.87, 104.37, 9732.54, 22842.96), (92595.40, 4141.72, 41248.52, 47205.16),
        (56197.15, 1967.01, 23505.88, 30724.26), (30006.82, 2638.01, 13842.09, 13526.72),
        (35804.04, 2379.82, 17232.36, 16191.86), (21984.78, 1877.33, 10250.21, 9857.24),
        (76469.67, 4950.52, 33641.72, 37877.43), (48055.86, 4289.38, 22034.83, 21731.65),
        (39366.55, 3547.51, 17088.95, 18730.09), (36425.78, 3083.59, 14453.54, 18888.65),
        (97277.77, 3831.44, 40695.15, 52751.18), (20352.51, 3019.37, 8072.94, 9260.20),
        (4832.05, 1000.11, 1095.79, 2736.15), (20363.19, 1378.27, 8328.79, 10656.13),
        (40678.13, 4426.66, 15322.72, 20928.75), (14806.45, 2159.54, 5755.54, 6891.37),
        (17881.12, 2498.86, 6957.44, 8424.82), (1477.63, 130.25, 628.37, 719.01),
        (24438.32, 1830.19, 12157.48, 10450.65), (8246.07, 921.30, 2794.67, 4530.10),
        (2865.23, 268.10, 1247.06, 1350.07), (3705.18, 279.85, 1650.26, 1775.07),
        (12199.08, 1692.09, 4922.97, 5584.02),
    ],
}

SOURCES = {
    2014: ("https://www.stats.gov.cn/sj/ndsj/2016/html/0309CH.jpg", "中国统计年鉴2016 表3-9 地区生产总值和指数", 2016, "现价。与2011–2012年Excel重叠的格子一致，故录入2014–2015年。"),
    2015: ("https://www.stats.gov.cn/sj/ndsj/2016/html/0309CH.jpg", "中国统计年鉴2016 表3-9 地区生产总值和指数", 2016, "现价。与2011–2012年Excel重叠的格子一致，故录入2014–2015年。"),
    2018: ("https://www.stats.gov.cn/sj/ndsj/2019/html/C0309.jpg", "中国统计年鉴2019 表3-9 地区生产总值(2018年)", 2019, "年鉴脚注：表中数据为初步核算数。仅保留三次产业之和与地区生产总值一致的行。"),
}


def accepted() -> list[dict]:
    kept = []
    rejected = []
    for year, rows in ROWS.items():
        if len(rows) != 31:
            raise SystemExit(f"{year} has {len(rows)} rows")
        url, table, book, note = SOURCES[year]
        for code, nums in zip(CODES, rows):
            gdp = float(nums[0])
            if len(nums) == 4:
                parts = sum(float(n) for n in nums[1:])
                if gdp == 0 or abs(parts - gdp) / gdp > 0.008:
                    rejected.append((year, code, gdp, parts))
                    continue
            kept.append(
                {
                    "indicator_id": "gdp",
                    "region_code": code,
                    "year": year,
                    "value": gdp,
                    "yearbook_year": book,
                    "source_url": url,
                    "source_table": table,
                    "scope_note": note,
                    "status": "初步" if "初步" in note else "未知",
                }
            )
    return kept, rejected


def main() -> None:
    kept, rejected = accepted()
    path = OUT / "gdp_gap_years.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(kept[0]))
        writer.writeheader()
        writer.writerows(kept)
    print(f"gdp gap kept {len(kept)} rejected {len(rejected)}")
    for item in rejected:
        print(" reject", item)


if __name__ == "__main__":
    main()
