from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def _frame() -> pd.DataFrame:
    frame = pd.read_csv(ROOT / "data" / "processed" / "observations.csv", dtype={"region_code": str})
    frame["region_code"] = frame["region_code"].str.replace(r"\.0$", "", regex=True).str.zfill(6)
    return frame


def test_pinned_official_cells():
    frame = _frame()
    pop = frame[(frame.indicator_id == "population") & (frame.region_code == "110000") & (frame.year == 2020)]
    assert len(pop) == 1
    assert abs(float(pop.iloc[0].value) - 2189) < 0.05
    national_2024 = frame[(frame.indicator_id == "population") & (frame.region_code == "000000") & (frame.year == 2024)]
    assert abs(float(national_2024.iloc[0].value) - 140828) < 0.05
    income = frame[(frame.indicator_id == "disposable-income") & (frame.region_code == "000000") & (frame.year == 2024)]
    assert abs(float(income.iloc[0].value) - 41314) < 0.6
    gdp = frame[(frame.indicator_id == "gdp") & (frame.region_code == "440000") & (frame.year == 2024)]
    assert abs(float(gdp.iloc[0].value) - 141633.8) < 0.2


def test_no_duplicate_keys_and_no_interpolation_marker():
    frame = _frame()
    assert not frame.duplicated(["indicator_id", "region_code", "year"]).any()
    assert frame["processing"].str.contains("插值").all()
    assert frame["source_url"].str.contains("stats.gov.cn").all()
