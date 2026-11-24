from pipeline.extract import classify_title
from pipeline.regions import match_region


def test_province_and_national_labels():
    assert match_region("北  京")["code"] == "110000"
    assert match_region("内蒙古")["code"] == "150000"
    assert match_region("黑龙江")["code"] == "230000"
    assert match_region("全  国")["code"] == "000000"
    assert match_region("总计")["code"] == "000000"
    assert match_region("香  港") is None
    assert match_region("注：2005年起为常住人口") is None


def test_titles_route_to_expected_kind():
    assert classify_title("2-5 分地区年末人口数") == "population"
    assert classify_title("3-9 地区生产总值(2020年)") == "gdp"
    assert classify_title("3-15 人均地区生产总值和指数") == "pcgdp"
    assert classify_title("3-1 国内生产总值") == "national_gdp"
    assert classify_title("6-18 分地区居民人均可支配收入") == "income"
    assert classify_title("6-24 分地区城镇居民人均可支配收入") is None
    assert classify_title("21-14 分地区普通本专科学生情况(2020年)") == "higher_ed"
    assert classify_title("21-14 分地区普通、职业本专科学生情况(2021年)") is None
    assert classify_title("22-3 每千人口卫生技术人员") == "physicians"
    assert classify_title("26-5 人口主要指标") is None
