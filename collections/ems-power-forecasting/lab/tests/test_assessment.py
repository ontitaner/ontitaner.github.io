# @AI_GENERATED
"""第 08 章一致性测试：预测考核口径与统计窗口。

锚定正文 08.x 手算（主线 30 MW 光伏，6 个成对预测/实测）：
  P_hat = [20, 25, 22, 18, 24, 26]，P_meas = [18, 24, 21, 18, 12, 14]
  -> e = [+2, +1, +1, 0, +12, +12]（后两点限电/检修，exclude=[F,F,F,F,T,T]）
  整月一起算 RMSE=7.0 -> 月准确率 76.6667%（不合格）
  分日平均 = 84.1242%（口径 B，仅对比，考核不用）
  剔除后 RMSE=sqrt(1.5) -> 95.9175%（合格）；合格率 4/4=100%
  上报率 2784/2880 = 96.6667%；考核判定 = {True, True, False}
边界：全剔除无有效样本、长度不一致、应报点数为 0。
"""
from __future__ import annotations

import pytest

from ems_lab.assessment import (
    assess,
    filter_valid,
    monthly_accuracy,
    monthly_accuracy_excluding,
    monthly_pass_rate,
    report_rate,
)
from ems_lab.error_metrics import root_mean_square_error

P_HAT = [20.0, 25.0, 22.0, 18.0, 24.0, 26.0]
P_MEAS = [18.0, 24.0, 21.0, 18.0, 12.0, 14.0]
EXCLUDE = [False, False, False, False, True, True]


def test_monthly_accuracy_whole_month():
    # 整月一起算 RMSE = sqrt(294/6) = 7 -> (1-7/30)*100
    assert monthly_accuracy(P_HAT, P_MEAS) == pytest.approx(76.66666667, abs=1e-6)


def test_monthly_accuracy_daily_average():
    # 口径 B：分日准确率再平均（仅对比）-> (94.7295+97.6430+60)/3 = 84.1242
    acc = []
    for a, b in [(0, 2), (2, 4), (4, 6)]:
        acc.append((1.0 - root_mean_square_error(P_HAT[a:b], P_MEAS[a:b]) / 30.0) * 100.0)
    assert sum(acc) / len(acc) == pytest.approx(84.12417154, abs=1e-6)


def test_filter_valid():
    pv, mv = filter_valid(P_HAT, P_MEAS, EXCLUDE)
    assert pv == [20.0, 25.0, 22.0, 18.0]
    assert mv == [18.0, 24.0, 21.0, 18.0]


def test_monthly_accuracy_excluding():
    # 剔除后 RMSE = sqrt(6/4) = sqrt(1.5) -> (1-sqrt(1.5)/30)*100
    assert monthly_accuracy_excluding(P_HAT, P_MEAS, EXCLUDE) == pytest.approx(95.91751709, abs=1e-6)


def test_monthly_pass_rate():
    # 剔除后 |e|=[2,1,1,0] 全 <= 2 -> 4/4*100 = 100
    assert monthly_pass_rate(P_HAT, P_MEAS, EXCLUDE) == pytest.approx(100.0, abs=1e-9)


def test_monthly_pass_rate_threshold_boundary():
    # |e|=2 恰好等于门槛，算合格
    assert monthly_pass_rate([2.0], [0.0], [False]) == pytest.approx(100.0, abs=1e-9)


def test_report_rate():
    assert report_rate(2784, 2880) == pytest.approx(96.66666667, abs=1e-6)


def test_assess():
    # 准确率 95.92 >= 80 ✅、合格率 100 >= 90 ✅、上报率 96.67 < 99 ❌
    verdict = assess(95.91751709, 100.0, 96.66666667)
    assert verdict == {"accuracy_ok": True, "pass_rate_ok": True, "report_rate_ok": False}


def test_assess_all_pass():
    verdict = assess(95.0, 95.0, 99.0)
    assert verdict == {"accuracy_ok": True, "pass_rate_ok": True, "report_rate_ok": True}


def test_invalid_inputs():
    with pytest.raises(ValueError):
        filter_valid([20.0], [18.0, 12.0], [False])          # 长度不一致
    with pytest.raises(ValueError):
        report_rate(100, 0)                                   # 应报点数为 0
    # 全剔除 -> 无有效样本，accuracy 抛 ValueError（由 error_metrics 兜底）
    with pytest.raises(ValueError):
        monthly_accuracy_excluding(P_HAT, P_MEAS, [True] * 6)
# @AI_GENERATED: end