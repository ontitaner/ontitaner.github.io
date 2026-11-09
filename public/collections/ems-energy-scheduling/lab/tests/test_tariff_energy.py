# @AI_GENERATED
"""一致性测试：分时电价 + 能量流 — 正文 01 章手算验证"""
import pytest

from lab.ems_lab.tariff import price_at, period_at, valley_hours, peak_hours
from lab.ems_lab.energy_flow import (stored_from_grid, out_from_stored,
                                     step_soc, ETA_CHG, ETA_DIS)


def test_price_at():
    assert price_at(0) == 0.35
    assert price_at(8) == 0.70
    assert price_at(10) == 1.20
    assert price_at(12) == 0.70
    assert price_at(23) == 0.35


def test_period_at():
    assert period_at(0) == "valley"
    assert period_at(8) == "flat"
    assert period_at(10) == "peak"


def test_valley_peak_hours():
    assert valley_hours() == [0, 1, 2, 3, 4, 5, 6, 7, 23]
    assert peak_hours() == [10, 11, 17, 18, 19, 20]


def test_energy_roundtrip():
    # 谷充 80MWh（电池侧），往返效率 0.9
    e_grid = 80.0 / ETA_CHG
    assert stored_from_grid(e_grid) == pytest.approx(80.0)
    assert out_from_stored(80.0) == pytest.approx(80.0 * ETA_DIS)


def test_step_soc_charge():
    # 充 1 小时 50MW：delta = 50*0.95/100 = +0.475
    assert step_soc(0.10, -50.0, 1.0) == pytest.approx(0.575)


def test_step_soc_discharge():
    # 放 1 小时 50MW：delta = -50/0.95/100 = -0.5263
    assert step_soc(0.90, 50.0, 1.0) == pytest.approx(0.90 - 50.0 / 0.95 / 100.0)
# @AI_GENERATED: end