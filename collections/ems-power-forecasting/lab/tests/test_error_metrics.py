# @AI_GENERATED
"""第 07 章一致性测试：预测误差指标（bias / MAE / RMSE / MAPE / 准确率 / 合格率）。

锚定正文 07.x 手算（主线 30 MW 光伏，6 个成对预测/实测）：
  P_hat = [9, 9, 15, 9, 6, 2]，P_meas = [6, 10, 16, 10, 6, 2]
  -> e = [+3, -1, -1, -1, 0, 0]
  bias = 0.0、MAE = 1.0、RMSE = sqrt(2) ≈ 1.41421356
  MAPE ≈ 12.7083%；准确率 ≈ 95.2860%；合格率（门槛 2 MW）≈ 83.3333%
边界：低出力爆炸、零分母 drop_zero、大误差放大、非法输入。
"""
from __future__ import annotations

import math

import pytest

from ems_lab.error_metrics import (
    accuracy_rmse,
    error_list,
    mean_absolute_error,
    mean_absolute_percentage_error,
    mean_error,
    pass_rate,
    root_mean_square_error,
)

P_HAT = [9.0, 9.0, 15.0, 9.0, 6.0, 2.0]
P_MEAS = [6.0, 10.0, 16.0, 10.0, 6.0, 2.0]


def test_error_list():
    assert error_list(P_HAT, P_MEAS) == [3.0, -1.0, -1.0, -1.0, 0.0, 0.0]


def test_mean_error():
    # bias = (3-1-1-1+0+0)/6 = 0（正负抵消）
    assert mean_error(P_HAT, P_MEAS) == pytest.approx(0.0, abs=1e-9)


def test_mean_absolute_error():
    # MAE = (3+1+1+1+0+0)/6 = 1.0
    assert mean_absolute_error(P_HAT, P_MEAS) == pytest.approx(1.0, abs=1e-9)


def test_root_mean_square_error():
    # RMSE = sqrt((9+1+1+1+0+0)/6) = sqrt(2)
    assert root_mean_square_error(P_HAT, P_MEAS) == pytest.approx(math.sqrt(2.0), abs=1e-9)


def test_mape():
    # MAPE = (3/6 + 1/10 + 1/16 + 1/10 + 0 + 0)/6 * 100 = 0.7625/6*100
    assert mean_absolute_percentage_error(P_HAT, P_MEAS) == pytest.approx(12.70833333, abs=1e-6)


def test_mape_low_output_explosion():
    # 加一个傍晚低出力点（误差 0.2 MW、占比 100%）-> MAPE 从 12.71% 拉到 25.18%
    mape = mean_absolute_percentage_error(P_HAT + [0.4], P_MEAS + [0.2])
    assert mape == pytest.approx(25.17857143, abs=1e-6)


def test_mape_zero_denominator_all_zero():
    # 全零实测：drop_zero 剔除后无有效样本 -> 返回 0.0（全零边界）
    assert mean_absolute_percentage_error([0.5], [0.0]) == pytest.approx(0.0, abs=1e-9)


def test_mape_drop_zero_skips_zero_point():
    # 含一个零实测点：该点被剔除，只对 (9, 6) 计算 -> 3/6*100 = 50%
    mape = mean_absolute_percentage_error([9.0, 0.5], [6.0, 0.0])
    assert mape == pytest.approx(50.0, abs=1e-9)


def test_accuracy_rmse():
    # 准确率 = (1 - sqrt(2)/30) * 100
    assert accuracy_rmse(P_HAT, P_MEAS) == pytest.approx(95.28595479, abs=1e-6)


def test_pass_rate():
    # 合格率（门槛 2 MW）：|e|=[3,1,1,1,0,0]，仅 |+3|>2 不合格 -> 5/6*100
    assert pass_rate(P_HAT, P_MEAS) == pytest.approx(83.33333333, abs=1e-6)


def test_pass_rate_threshold_boundary():
    # |e|=2 恰好等于门槛，算合格（>= 不算越限）
    assert pass_rate([2.0], [0.0], threshold=2.0) == pytest.approx(100.0, abs=1e-9)
    assert pass_rate([2.1], [0.0], threshold=2.0) == pytest.approx(0.0, abs=1e-9)


def test_rmse_amplifies_large_error():
    # 误差 +3 改 +10：MAE=13/6，RMSE=sqrt(103/6)（RMSE 涨得更狠）
    big_hat = [16.0, 9.0, 15.0, 9.0, 6.0, 2.0]
    assert mean_absolute_error(big_hat, P_MEAS) == pytest.approx(13.0 / 6.0, abs=1e-9)
    assert root_mean_square_error(big_hat, P_MEAS) == pytest.approx(math.sqrt(103.0 / 6.0), abs=1e-9)


def test_invalid_inputs():
    with pytest.raises(ValueError):
        error_list([2.0], [2.6, 3.4])                       # 长度不一致
    with pytest.raises(ValueError):
        mean_absolute_error([], [])                          # 空序列
    with pytest.raises(ValueError):
        accuracy_rmse(P_HAT, P_MEAS, p_nom=0.0)              # 非法装机容量
    with pytest.raises(ValueError):
        pass_rate(P_HAT, P_MEAS, threshold=-1.0)             # 非法门槛
# @AI_GENERATED: end