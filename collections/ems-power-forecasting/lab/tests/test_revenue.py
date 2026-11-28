# @AI_GENERATED
"""第 09 章一致性测试：锚定正文手算数值。

完美日套利 85.0 千元、低估 6 MW x 2h 损失 10.2 千元、
外推 6.7 万元 = 78.8235 MWh、4 时段累积 40.8 千元。
"""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ems_lab.revenue import (  # noqa: E402
    arbitrage_gain_k,
    daily_loss_k,
    error_energy_mwh,
    schedule_loss_k,
)


def test_arbitrage_gain():
    assert arbitrage_gain_k(100.0, 100.0) == pytest.approx(85.0)  # 8.5 万元


def test_error_energy():
    assert error_energy_mwh(-6.0, 2.0) == pytest.approx(12.0)
    assert error_energy_mwh(6.0, 2.0) == pytest.approx(12.0)  # 高估对称


def test_schedule_loss():
    assert schedule_loss_k(-6.0, 2.0) == pytest.approx(10.2)  # 1.02 万元
    assert schedule_loss_k(6.0, 2.0) == pytest.approx(10.2)  # 高估同量


def test_daily_loss():
    # 4 个低估时段各 -6 MW x 2h -> 4 x 10.2 = 40.8 千元 = 4.08 万元
    assert daily_loss_k([-6.0, -6.0, -6.0, -6.0], [2.0, 2.0, 2.0, 2.0]) == pytest.approx(40.8)


def test_daily_loss_empty():
    assert daily_loss_k([], []) == pytest.approx(0.0)


def test_invalid():
    with pytest.raises(ValueError):
        arbitrage_gain_k(-100.0, 100.0)
    with pytest.raises(ValueError):
        error_energy_mwh(-6.0, -2.0)
    with pytest.raises(ValueError):
        daily_loss_k([-6.0], [2.0, 2.0])