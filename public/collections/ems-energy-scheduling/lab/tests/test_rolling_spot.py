# @AI_GENERATED
"""一致性测试：日内滚动修正 + 现货报价 — 正文 06/07 章手算验证"""
import pytest

from lab.ems_lab.rolling import arbitrage_profit, fixed_plan_profit, mape
from lab.ems_lab.spot import should_discharge, bid_price


def test_rolling_fixed_vs_ideal():
    forecast = [350.0, 700.0, 1200.0]   # 谷、A(平)、B(峰)
    actual = [350.0, 1300.0, 1200.0]    # A 涨过峰段
    fixed = fixed_plan_profit(forecast, actual)
    ideal = arbitrage_profit(actual)
    assert fixed == pytest.approx(76.0 * 1200.0 - 80.0 / 0.95 * 350.0)
    assert ideal == pytest.approx(76.0 * 1300.0 - 80.0 / 0.95 * 350.0)
    assert ideal - fixed == pytest.approx(7600.0)


def test_mape():
    assert mape([100.0, 200.0], [110.0, 180.0]) == pytest.approx(
        (abs(10 / 110) + abs(20 / 180)) / 2 * 100.0)


def test_spot_should_discharge():
    assert should_discharge(600.0, 450.0) is True
    assert should_discharge(400.0, 450.0) is False


def test_spot_bid_price():
    assert bid_price(450.0, 600.0, 0.1) == 660.0
    assert bid_price(450.0, 400.0, 0.1) == 450.0
# @AI_GENERATED: end