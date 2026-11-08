# @AI_GENERATED
"""一致性测试：月度考核评分 — 正文 07 章手算验证

正文 07.4 手算：VQR=97%, 投运率=98.7%, T_avg=22s
S_month = 90.0×0.5 + 100×0.3 + 76.7×0.2 = 86.9
"""
from lab.ems_lab.scoring import monthly_score, s_voltage, s_availability, s_performance


def test_s_voltage_vqr_97():
    assert abs(s_voltage(0.9564) - 83.2) < 0.1


def test_s_availability_98_7():
    assert abs(s_availability(0.987) - 100.0) < 0.1


def test_s_performance_t22():
    assert abs(s_performance(22) - 76.7) < 0.2


def test_monthly_score():
    score = monthly_score(vqr=0.9564, availability=0.987, t_avg_s=22)
    assert abs(score - 86.9) < 0.2


def test_monthly_score_components():
    sv = s_voltage(0.9564)
    sa = s_availability(0.987)
    sq = s_performance(22)
    score = sv * 0.5 + sa * 0.3 + sq * 0.2
    assert abs(score - 86.9) < 0.2
# @AI_GENERATED: end