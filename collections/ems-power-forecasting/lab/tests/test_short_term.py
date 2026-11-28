# @AI_GENERATED
"""第 05 章一致性测试：短期功率预测（物理基值 + 分箱偏差修正）。

锚定正文 05.x 手算（主线 30 MW 光伏）：
  NWP GHI=800、T_amb=20 -> 物理预测 P_phys = 20.404 MW（复用 03.4）
  历史 6 样本、边界 [5, 20] -> 箱偏差 bias = [+0.5, -0.9, -2.25]
  最终预测 P_hat = 20.404 - 2.25 = 18.154 MW
  边界语义：P_phys=5.0 归箱2（5 ≤ x < 20）；P_phys=20.0 归箱3（x ≥ 20）
"""
from __future__ import annotations

import pytest

from ems_lab.shortterm import (
    _bin_index,
    bias_correct,
    fit_bin_bias,
    physical_forecast,
    short_term_forecast,
)

P_PHYS = [2.0, 3.0, 10.0, 15.0, 24.0, 26.0]
P_MEAS = [2.6, 3.4, 9.2, 14.0, 22.0, 23.5]
BIN_EDGES = [5.0, 20.0]


def test_physical_forecast_main_case():
    # GHI=800、T_amb=20 -> 20.404（对齐 03.4 手算）
    assert physical_forecast(800.0, 20.0) == pytest.approx(20.404, abs=1e-9)


def test_fit_bin_bias():
    bias = fit_bin_bias(P_PHYS, P_MEAS, BIN_EDGES)
    assert bias == pytest.approx([0.5, -0.9, -2.25], abs=1e-9)


def test_bin_index_boundary():
    assert _bin_index(4.99, BIN_EDGES) == 0
    assert _bin_index(5.0, BIN_EDGES) == 1     # 边界 5 归箱2
    assert _bin_index(19.99, BIN_EDGES) == 1
    assert _bin_index(20.0, BIN_EDGES) == 2    # 边界 20 归箱3


def test_bias_correct_boundary():
    bias = [0.5, -0.9, -2.25]
    assert bias_correct(3.0, BIN_EDGES, bias) == pytest.approx(3.5)      # 低出力 +0.5
    assert bias_correct(5.0, BIN_EDGES, bias) == pytest.approx(4.1)      # 5 - 0.9
    assert bias_correct(20.0, BIN_EDGES, bias) == pytest.approx(17.75)   # 20 - 2.25
    assert bias_correct(20.404, BIN_EDGES, bias) == pytest.approx(18.154, abs=1e-9)


def test_short_term_forecast_main_case():
    bias = [0.5, -0.9, -2.25]
    assert short_term_forecast(800.0, 20.0, BIN_EDGES, bias) == pytest.approx(18.154, abs=1e-9)


def test_fit_bin_bias_empty_bin_zero():
    # 箱2 [5,20) 无样本 -> 偏差记 0.0（无样本不修正）
    bias = fit_bin_bias([2.0, 24.0], [2.6, 22.0], BIN_EDGES)
    assert bias == pytest.approx([0.6, 0.0, -2.0], abs=1e-9)


def test_invalid_inputs():
    with pytest.raises(ValueError):
        fit_bin_bias([2.0], [2.6, 3.4], BIN_EDGES)          # 物理/实测长度不一致
    with pytest.raises(ValueError):
        fit_bin_bias(P_PHYS, P_MEAS, [20.0, 5.0])            # 边界非升序
    with pytest.raises(ValueError):
        bias_correct(20.404, BIN_EDGES, [0.5, -0.9])         # bias 箱数不匹配
# @AI_GENERATED: end