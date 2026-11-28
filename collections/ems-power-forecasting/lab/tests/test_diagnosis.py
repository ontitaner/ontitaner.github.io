# @AI_GENERATED
"""第 14 章一致性测试：锚定正文手算数值与边界语义。

四类根因签名：孤立尖刺 [0,0,12,0,0,0]->True；持续同号 [+2,+1,+1,+2,+1,+2]->True、
[-2,-1,-2,-2,-1,-2]->True；天气骤变 -80 vs -400->True；测点偏低 每点-80->True。
综合判定 diagnose_root_cause 逐类反推：数据污染/模型漂移/天气骤变/测点问题/unknown。
"""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ems_lab.diagnosis import (  # noqa: E402
    check_data_poison,
    check_model_drift,
    check_sensor_anomaly,
    check_weather_spike,
    diagnose_root_cause,
)

E_POLLUTION = [0.0, 0.0, 12.0, 0.0, 0.0, 0.0]
E_WEATHER = [0.0, 0.0, 8.0, -4.0, 5.0, 0.0]
E_DRIFT = [2.0, 1.0, 1.0, 2.0, 1.0, 2.0]
E_METER = [-2.0, -1.0, -2.0, -2.0, -1.0, -2.0]
REF_GHI = [800.0, 780.0, 760.0, 740.0, 720.0, 700.0]
MEAS_GHI = [720.0, 700.0, 680.0, 660.0, 640.0, 620.0]  # 每点低 80


def test_check_data_poison_main():
    # 14.3 主案例：点3 孤立尖刺（邻居都正常）
    assert check_data_poison(E_POLLUTION) is True


def test_check_data_poison_boundary_equal():
    # 边界语义：|e| 恰好等于阈值 10 算尖刺（>= 不是 >）
    assert check_data_poison([0.0, 10.0, 0.0]) is True


def test_check_data_poison_persistent():
    # 全段抬高（漂移/脏污）不孤立
    assert check_data_poison([12.0, 12.0, 12.0, 12.0, 12.0, 12.0]) is False


def test_check_data_poison_no_spike():
    # 无 >= 10 的点
    assert check_data_poison(E_DRIFT) is False


def test_check_weather_spike_main():
    # 14.5 主案例：实测 -400、NWP -80 -> 320 >= 300 -> True
    assert check_weather_spike(-80.0, -400.0) is True


def test_check_weather_spike_boundary_equal():
    # 边界语义：差值恰好等于阈值 300 算骤变（>=）
    assert check_weather_spike(-100.0, -400.0) is True


def test_check_weather_spike_normal():
    # 差值小，NWP 基本预报到了 -> False
    assert check_weather_spike(-80.0, -100.0) is False


def test_check_model_drift_main():
    # 14.4 主案例：持续同号 + drift 触发 -> True
    assert check_model_drift(E_DRIFT, True) is True


def test_check_model_drift_no_drift():
    # 持续同号但漂移未触发 -> False
    assert check_model_drift(E_DRIFT, False) is False


def test_check_model_drift_mixed():
    # 有正有负（不持续同号）即便 drift 触发也不判模型漂移
    assert check_model_drift([2.0, -1.0, 1.0], True) is False


def test_check_sensor_anomaly_main():
    # 14.4 主案例：持续同号 + 实测每点低 80 -> True
    assert check_sensor_anomaly(E_METER, MEAS_GHI, REF_GHI) is True


def test_check_sensor_anomaly_boundary_equal():
    # 边界语义：每点恰好低 60 也算脏污（<= -60）
    assert check_sensor_anomaly([-1.0, -2.0], [740.0, 720.0], [800.0, 780.0]) is True


def test_check_sensor_anomaly_normal():
    # 实测与参考基本一致 -> False
    assert check_sensor_anomaly(E_METER, [800.0] * 6, [800.0] * 6) is False


def test_check_sensor_anomaly_length_mismatch():
    # 长度不一致 -> False
    assert check_sensor_anomaly(E_METER, [720.0], REF_GHI) is False


def test_diagnose_pollution():
    cause, _ = diagnose_root_cause(E_POLLUTION, -80.0, -100.0,
                                    [800.0] * 6, [800.0] * 6, False)
    assert cause == "data_pollution"


def test_diagnose_weather():
    cause, _ = diagnose_root_cause(E_WEATHER, -80.0, -400.0,
                                    [800.0] * 6, [800.0] * 6, False)
    assert cause == "weather_abrupt"


def test_diagnose_model_drift():
    cause, _ = diagnose_root_cause(E_DRIFT, -80.0, -100.0,
                                    [800.0] * 6, [800.0] * 6, True)
    assert cause == "model_drift"


def test_diagnose_meter_problem():
    cause, _ = diagnose_root_cause(E_METER, -80.0, -100.0,
                                    MEAS_GHI, REF_GHI, False)
    assert cause == "meter_problem"


def test_diagnose_unknown_systematic_no_sidechannel():
    # 持续同号但 drift=False、实测不偏低 -> unknown（人工复核）
    cause, _ = diagnose_root_cause(E_DRIFT, -80.0, -100.0,
                                    [800.0] * 6, [800.0] * 6, False)
    assert cause == "unknown"


def test_diagnose_unknown_no_match():
    # 无任何签名 -> unknown
    cause, _ = diagnose_root_cause([0.0] * 6, -80.0, -100.0,
                                    [800.0] * 6, [800.0] * 6, False)
    assert cause == "unknown"