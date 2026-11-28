# @AI_GENERATED
"""第 10 章一致性测试：锚定正文手算数值。

云团覆盖高估 4 MW x 2h 偏差电量 8.0 MWh、结算损失 8.0 千元（0.8 万元）、
低估一阶近似对称 8.0 千元、无偏差 0、8 个 15min 时段累积 8.0 千元。
"""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ems_lab.settlement import (  # noqa: E402
    daily_deviation_loss_k,
    deviation_energy_mwh,
    deviation_loss_k,
)


def test_deviation_energy():
    assert deviation_energy_mwh(16.0, 12.0, 2.0) == pytest.approx(8.0)  # 高估 4 MW x 2h
    assert deviation_energy_mwh(12.0, 16.0, 2.0) == pytest.approx(8.0)  # 低估对称


def test_deviation_loss():
    assert deviation_loss_k(16.0, 12.0, 2.0) == pytest.approx(8.0)  # 0.8 万元
    assert deviation_loss_k(12.0, 16.0, 2.0) == pytest.approx(8.0)  # 一阶近似同量
    assert deviation_loss_k(16.0, 16.0, 2.0) == pytest.approx(0.0)  # 无偏差


def test_daily_deviation_loss():
    # 8 个 15min 结算时段，云团覆盖期间各高估 4 MW x 0.25h = 1 MWh -> 8 x 1.0 = 8.0 千元
    assert daily_deviation_loss_k([16.0] * 8, [12.0] * 8, [0.25] * 8) == pytest.approx(8.0)


def test_daily_deviation_loss_empty():
    assert daily_deviation_loss_k([], [], []) == pytest.approx(0.0)


def test_invalid():
    with pytest.raises(ValueError):
        deviation_energy_mwh(16.0, 12.0, -2.0)
    with pytest.raises(ValueError):
        daily_deviation_loss_k([16.0], [12.0], [0.25, 0.25])