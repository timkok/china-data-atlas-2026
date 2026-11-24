"""Mainland provincial regions and documented groupings.

Coverage is the 31 provincial-level regions of mainland China.
Hong Kong, Macao and Taiwan are outside this product's statistical
coverage. Their absence is a coverage choice, not a statement about
territorial status.

Region codes follow GB/T 2260 6-digit provincial codes.
`000000` / 全国 is an aggregate used by NBS tables. It is not a GB/T 2260
code.
"""

from __future__ import annotations

REGIONS: list[dict] = [
    {"code": "110000", "name_zh": "北京市", "name_en": "Beijing", "short": "北京", "macro": "north", "nbs": "east"},
    {"code": "120000", "name_zh": "天津市", "name_en": "Tianjin", "short": "天津", "macro": "north", "nbs": "east"},
    {"code": "130000", "name_zh": "河北省", "name_en": "Hebei", "short": "河北", "macro": "north", "nbs": "east"},
    {"code": "140000", "name_zh": "山西省", "name_en": "Shanxi", "short": "山西", "macro": "north", "nbs": "central"},
    {"code": "150000", "name_zh": "内蒙古自治区", "name_en": "Inner Mongolia", "short": "内蒙古", "macro": "north", "nbs": "west"},
    {"code": "210000", "name_zh": "辽宁省", "name_en": "Liaoning", "short": "辽宁", "macro": "northeast", "nbs": "northeast"},
    {"code": "220000", "name_zh": "吉林省", "name_en": "Jilin", "short": "吉林", "macro": "northeast", "nbs": "northeast"},
    {"code": "230000", "name_zh": "黑龙江省", "name_en": "Heilongjiang", "short": "黑龙江", "macro": "northeast", "nbs": "northeast"},
    {"code": "310000", "name_zh": "上海市", "name_en": "Shanghai", "short": "上海", "macro": "east", "nbs": "east"},
    {"code": "320000", "name_zh": "江苏省", "name_en": "Jiangsu", "short": "江苏", "macro": "east", "nbs": "east"},
    {"code": "330000", "name_zh": "浙江省", "name_en": "Zhejiang", "short": "浙江", "macro": "east", "nbs": "east"},
    {"code": "340000", "name_zh": "安徽省", "name_en": "Anhui", "short": "安徽", "macro": "east", "nbs": "central"},
    {"code": "350000", "name_zh": "福建省", "name_en": "Fujian", "short": "福建", "macro": "east", "nbs": "east"},
    {"code": "360000", "name_zh": "江西省", "name_en": "Jiangxi", "short": "江西", "macro": "east", "nbs": "central"},
    {"code": "370000", "name_zh": "山东省", "name_en": "Shandong", "short": "山东", "macro": "east", "nbs": "east"},
    {"code": "410000", "name_zh": "河南省", "name_en": "Henan", "short": "河南", "macro": "central", "nbs": "central"},
    {"code": "420000", "name_zh": "湖北省", "name_en": "Hubei", "short": "湖北", "macro": "central", "nbs": "central"},
    {"code": "430000", "name_zh": "湖南省", "name_en": "Hunan", "short": "湖南", "macro": "central", "nbs": "central"},
    {"code": "440000", "name_zh": "广东省", "name_en": "Guangdong", "short": "广东", "macro": "south", "nbs": "east"},
    {"code": "450000", "name_zh": "广西壮族自治区", "name_en": "Guangxi", "short": "广西", "macro": "south", "nbs": "west"},
    {"code": "460000", "name_zh": "海南省", "name_en": "Hainan", "short": "海南", "macro": "south", "nbs": "east"},
    {"code": "500000", "name_zh": "重庆市", "name_en": "Chongqing", "short": "重庆", "macro": "southwest", "nbs": "west"},
    {"code": "510000", "name_zh": "四川省", "name_en": "Sichuan", "short": "四川", "macro": "southwest", "nbs": "west"},
    {"code": "520000", "name_zh": "贵州省", "name_en": "Guizhou", "short": "贵州", "macro": "southwest", "nbs": "west"},
    {"code": "530000", "name_zh": "云南省", "name_en": "Yunnan", "short": "云南", "macro": "southwest", "nbs": "west"},
    {"code": "540000", "name_zh": "西藏自治区", "name_en": "Tibet", "short": "西藏", "macro": "southwest", "nbs": "west"},
    {"code": "610000", "name_zh": "陕西省", "name_en": "Shaanxi", "short": "陕西", "macro": "northwest", "nbs": "west"},
    {"code": "620000", "name_zh": "甘肃省", "name_en": "Gansu", "short": "甘肃", "macro": "northwest", "nbs": "west"},
    {"code": "630000", "name_zh": "青海省", "name_en": "Qinghai", "short": "青海", "macro": "northwest", "nbs": "west"},
    {"code": "640000", "name_zh": "宁夏回族自治区", "name_en": "Ningxia", "short": "宁夏", "macro": "northwest", "nbs": "west"},
    {"code": "650000", "name_zh": "新疆维吾尔自治区", "name_en": "Xinjiang", "short": "新疆", "macro": "northwest", "nbs": "west"},
]

NATIONAL = {
    "code": "000000",
    "name_zh": "全国",
    "name_en": "China (national total published by NBS)",
    "short": "全国",
    "macro": None,
    "nbs": None,
}

# Aliases ordered longest-first so 黑龙江 matches before any shorter token.
_ALIASES: list[tuple[str, dict]] = []
for region in REGIONS:
    for alias in (
        region["name_zh"],
        region["short"],
        region["name_zh"].replace("省", "").replace("市", ""),
    ):
        _ALIASES.append((alias, region))
_ALIASES.append(("内蒙古", REGIONS[4]))
_ALIASES.append(("广西", REGIONS[19]))
_ALIASES.append(("宁夏", REGIONS[29]))
_ALIASES.append(("新疆", REGIONS[30]))
_ALIASES.append(("西藏", REGIONS[25]))
_ALIASES.sort(key=lambda item: len(item[0]), reverse=True)

NATIONAL_ALIASES = ("全国", "总计", "合计")

MACRO_REGIONS = [
    {"id": "north", "name_zh": "华北", "name_en": "North China", "members": ["110000", "120000", "130000", "140000", "150000"]},
    {"id": "northeast", "name_zh": "东北", "name_en": "Northeast China", "members": ["210000", "220000", "230000"]},
    {"id": "east", "name_zh": "华东", "name_en": "East China", "members": ["310000", "320000", "330000", "340000", "350000", "360000", "370000"]},
    {"id": "central", "name_zh": "华中", "name_en": "Central China", "members": ["410000", "420000", "430000"]},
    {"id": "south", "name_zh": "华南", "name_en": "South China", "members": ["440000", "450000", "460000"]},
    {"id": "southwest", "name_zh": "西南", "name_en": "Southwest China", "members": ["500000", "510000", "520000", "530000", "540000"]},
    {"id": "northwest", "name_zh": "西北", "name_en": "Northwest China", "members": ["610000", "620000", "630000", "640000", "650000"]},
]

# NBS four-region grouping used in household survey releases since 2011.
# Inner Mongolia is West here and North in the seven-region geographic grouping.
NBS_REGIONS = [
    {"id": "east", "name_zh": "东部", "name_en": "East (NBS)", "members": ["110000", "120000", "130000", "310000", "320000", "330000", "350000", "370000", "440000", "460000"]},
    {"id": "central", "name_zh": "中部", "name_en": "Central (NBS)", "members": ["140000", "340000", "360000", "410000", "420000", "430000"]},
    {"id": "west", "name_zh": "西部", "name_en": "West (NBS)", "members": ["150000", "450000", "500000", "510000", "520000", "530000", "540000", "610000", "620000", "630000", "640000", "650000"]},
    {"id": "northeast", "name_zh": "东北", "name_en": "Northeast (NBS)", "members": ["210000", "220000", "230000"]},
]

BY_CODE = {region["code"]: region for region in REGIONS}
BY_CODE[NATIONAL["code"]] = NATIONAL


def normalize_label(text: str) -> str:
    if text is None:
        return ""
    cleaned = str(text)
    for token in ("\u3000", "\xa0", " ", "\n", "\r", "\t", "省", "市"):
        cleaned = cleaned.replace(token, "")
    return cleaned.strip()


def match_region(label: str) -> dict | None:
    """Match a yearbook row label to a province or the national aggregate."""
    text = normalize_label(label)
    if not text:
        return None
    if text in NATIONAL_ALIASES:
        return NATIONAL
    # Reject explicit non-coverage labels rather than fuzzy-matching them.
    for blocked in ("香港", "澳门", "台灣", "台湾"):
        if blocked in text:
            return None
    for alias, region in _ALIASES:
        if alias in text:
            return region
    return None
