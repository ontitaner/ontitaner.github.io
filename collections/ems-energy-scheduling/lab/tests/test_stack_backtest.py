# @AI_GENERATED
"""一致性测试：辅助服务叠加 + 收益复盘 — 正文 08/09 章手算验证"""
from lab.ems_lab.stack import capacity_split
from lab.ems_lab.backtest import net_profit, attribution


def test_capacity_split():
    assert capacity_split(50.0, 10.0, 0.0) == {
        "pfr": 10.0, "volt": 0.0, "arbitrage": 40.0, "total": 50.0}


def test_capacity_split_with_volt():
    r = capacity_split(50.0, 10.0, 5.0)
    assert r == {"pfr": 10.0, "volt": 5.0, "arbitrage": 35.0, "total": 50.0}


def test_net_profit():
    assert net_profit(91200.0, 29474.0, 5000.0) == 56726.0


def test_attribution():
    r = attribution(61726.0, 46526.0, {"price": -11800.0, "energy": -3400.0})
    assert r["gap"] == -15200.0
    assert r["explained"] == -15200.0
    assert r["residual"] == 0.0
    assert r["check"] is True
# @AI_GENERATED: end