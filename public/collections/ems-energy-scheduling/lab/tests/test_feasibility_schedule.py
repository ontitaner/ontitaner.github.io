# @AI_GENERATED
"""一致性测试：可行域 + 日前排程 — 正文 04/05 章手算验证"""
import pytest

from lab.ems_lab.feasibility import available_energy, feasible_p
from lab.ems_lab.schedule import one_cycle, two_cycle


def test_available_energy():
    assert available_energy(0.90) == (80.0, 0.0)
    assert available_energy(0.10) == (0.0, 80.0)
    assert available_energy(0.50) == (40.0, 40.0)


def test_feasible_p_full():
    assert feasible_p(0.90, 1.0) == (50.0, 0.0)
    assert feasible_p(0.10, 1.0) == (0.0, 50.0)


def test_feasible_p_partial():
    # soc=0.5，dt=1h：放电 40*0.95=38，充电 40/0.95=42.105
    p_dis, p_chg = feasible_p(0.50, 1.0)
    assert p_dis == pytest.approx(38.0)
    assert p_chg == pytest.approx(40.0 / 0.95)


def test_one_cycle():
    r = one_cycle(80.0)
    assert r["e_grid"] == pytest.approx(80.0 / 0.95)
    assert r["e_out"] == pytest.approx(76.0)
    assert r["cost"] == pytest.approx(80.0 / 0.95 * 350.0)
    assert r["revenue"] == pytest.approx(76.0 * 1200.0)
    assert r["profit"] == pytest.approx(76.0 * 1200.0 - 80.0 / 0.95 * 350.0)


def test_two_cycle():
    r = two_cycle(80.0)
    first_profit = 76.0 * 1200.0 - 80.0 / 0.95 * 350.0
    second_profit = 76.0 * 1200.0 - 80.0 / 0.95 * 700.0
    assert r["first"]["profit"] == pytest.approx(first_profit)
    assert r["second"]["profit"] == pytest.approx(second_profit)
    assert r["profit"] == pytest.approx(first_profit + second_profit)
# @AI_GENERATED: end