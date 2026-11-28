# @AI_GENERATED
"""第 06 章一致性测试：超短期功率预测（持续法 + 滚动外推）。

锚定正文 06.x 手算（主线 30 MW 光伏，15min 网格）：
  持续法 P_meas(t)=18.0 -> [18, 18, 18, 18]
  滚动外推 [16, 17, 18] -> Δ=+1 -> [19, 20, 21, 22]
  滚动更新 18.5 -> 窗口 [17, 18, 18.5] -> Δ=+0.5 -> [19.0, 19.5, 20.0, 20.5]
  触顶 clamp [22, 24] -> [25, 25, 25, 25]；触底 clamp [5, 3] -> [1, 0, 0]
  退化（历史不足 2 点）-> 退化为持续法
"""
from __future__ import annotations

import pytest

from ems_lab.ultraterm import (
    _trend_slope,
    persistence_forecast,
    roll_window,
    rolling_extrapolate,
)


def test_persistence_forecast():
    assert persistence_forecast(18.0, 4) == [18.0, 18.0, 18.0, 18.0]


def test_trend_slope():
    assert _trend_slope([16.0, 17.0, 18.0]) == pytest.approx(1.0)
    assert _trend_slope([17.0, 18.0, 18.5]) == pytest.approx(0.5)
    assert _trend_slope([18.0]) == pytest.approx(0.0)       # 不足 2 点退化


def test_rolling_extrapolate_main():
    assert rolling_extrapolate([16.0, 17.0, 18.0], 4) == [19.0, 20.0, 21.0, 22.0]


def test_rolling_update():
    hist2 = roll_window([16.0, 17.0, 18.0], 18.5)
    assert hist2 == [17.0, 18.0, 18.5]
    assert rolling_extrapolate(hist2, 4) == [19.0, 19.5, 20.0, 20.5]


def test_clamp_upper():
    # 触顶：外推到 26/28/30/32 均被截到 25
    assert rolling_extrapolate([22.0, 24.0], 4) == [25.0, 25.0, 25.0, 25.0]


def test_clamp_lower():
    # 触底：外推到负值被截到 0（光伏只发不收）
    assert rolling_extrapolate([5.0, 3.0], 3) == [1.0, 0.0, 0.0]


def test_degenerate_single_point():
    # 历史不足 2 点 -> Δ=0 -> 退化为持续法
    assert rolling_extrapolate([18.0], 4) == [18.0, 18.0, 18.0, 18.0]


def test_invalid_inputs():
    with pytest.raises(ValueError):
        rolling_extrapolate([], 4)                          # 空历史
    with pytest.raises(ValueError):
        persistence_forecast(18.0, -1)                      # 负步数
    with pytest.raises(ValueError):
        rolling_extrapolate([16.0, 17.0], 4, p_max=0.0)     # 非法上限
    with pytest.raises(ValueError):
        roll_window([16.0], 17.0, max_len=0)                # 非法窗口长度
# @AI_GENERATED: end