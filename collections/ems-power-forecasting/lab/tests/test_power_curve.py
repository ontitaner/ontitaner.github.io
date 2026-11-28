# @AI_GENERATED
"""第 03 章一致性测试：风速 -> 风机出力转换（四区功率曲线 + 饱和区）。

锚定正文 03.x 手算（教学示例单机 2.5 MW、v_ci=3、v_r=12、v_co=25）：
  v=6 -> (216−27)/(1728−27) = 1/9 -> 0.2778 MW（半额定风速只发额定 1/9）
  v=9 -> 702/1701 ≈ 0.4127 -> 1.032 MW
  v=12~25 -> 2.5 MW（饱和）；v=2 或 v=26 -> 0
"""
from __future__ import annotations

import pytest

from ems_lab.power_curve import wind_power


def test_below_cutin():
    assert wind_power(2.0) == pytest.approx(0.0)


def test_at_cutin_boundary():
    # v == v_ci -> 0（刚到切入风速，不发电）
    assert wind_power(3.0) == pytest.approx(0.0)


def test_cubic_region_half_speed():
    # v=6（半额定风速）-> 1/9 额定 ≈ 0.2778 MW（三次方非线性，不是一半）
    assert wind_power(6.0) == pytest.approx(2.5 / 9.0, rel=1e-6)


def test_cubic_region_three_quarters():
    # v=9（3/4 额定风速）-> 702/1701 额定 ≈ 1.032 MW
    assert wind_power(9.0) == pytest.approx(2.5 * 702.0 / 1701.0, rel=1e-6)


def test_rated_speed():
    # v == v_r -> 恰好额定
    assert wind_power(12.0) == pytest.approx(2.5)


def test_saturation_region():
    # 额定风速以上恒定 2.5 MW（饱和/变桨保持）
    assert wind_power(18.0) == pytest.approx(2.5)


def test_at_cutout_boundary():
    # v == v_co -> 仍满发（超过才切出）
    assert wind_power(25.0) == pytest.approx(2.5)


def test_above_cutout():
    assert wind_power(26.0) == pytest.approx(0.0)


def test_invalid_inputs():
    with pytest.raises(ValueError):
        wind_power(-1.0)
    with pytest.raises(ValueError):
        wind_power(6.0, p_rated=-1.0)
    with pytest.raises(ValueError):
        wind_power(6.0, v_ci=12.0, v_r=3.0, v_co=25.0)
# @AI_GENERATED: end