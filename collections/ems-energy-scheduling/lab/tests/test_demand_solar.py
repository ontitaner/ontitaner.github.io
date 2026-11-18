# @AI_GENERATED
"""一致性测试：需量管理 + 光储协同 — 正文 02/03 章手算验证"""
import math

from lab.ems_lab.demand import peak_demand, demand_charge, shave, shaved_peak
from lab.ems_lab.solar import pv_curve, moving_average, bess_for_smoothing, track_error


def test_peak_demand():
    assert peak_demand([3.0, 5.0, 7.0, 6.0]) == 7.0


def test_demand_charge():
    assert demand_charge(7.0, 40.0) == 280000.0


def test_shave():
    # 目标需量 5MW、BESS 放电上限 2MW
    assert shave([3.0, 5.0, 7.0, 6.0], 2.0, 5.0) == [0.0, 0.0, 2.0, 1.0]


def test_shaved_peak():
    assert shaved_peak([3.0, 5.0, 7.0, 6.0], [0.0, 0.0, 2.0, 1.0]) == 5.0


def test_pv_curve():
    assert pv_curve(6.0) == 0.0
    assert pv_curve(12.0) == 30.0
    assert pv_curve(20.0) == 0.0


def test_moving_average():
    assert moving_average([1, 2, 3, 4, 5], 3) == [1.5, 2.0, 3.0, 4.0, 4.5]


def test_bess_for_smoothing():
    assert bess_for_smoothing([1, 2, 3, 4, 5], 3) == [0.5, 0.0, 0.0, 0.0, -0.5]


def test_track_error():
    assert track_error([100.0, 100.0], [98.0, 103.0]) == [-2.0, 3.0]
# @AI_GENERATED: end