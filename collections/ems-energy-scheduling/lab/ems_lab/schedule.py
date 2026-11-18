# @AI_GENERATED
"""日前充放电排程（分段电价贪心最优）

对应章节：01 峰谷套利（一充一放），05 日前优化（两充两放）

约定（附录B）：能量 MWh，电价元/MWh，放电为正。
"""
from __future__ import annotations

PRICE_VALLEY = 350.0  # 元/MWh
PRICE_FLAT = 700.0
PRICE_PEAK = 1200.0


def _calc(e_stored: float, buy_price: float, sell_price: float,
          eta_chg: float, eta_dis: float) -> dict:
    e_grid = e_stored / eta_chg
    e_out = e_stored * eta_dis
    cost = e_grid * buy_price
    revenue = e_out * sell_price
    return dict(e_grid=e_grid, e_out=e_out, cost=cost,
                revenue=revenue, profit=revenue - cost)


def one_cycle(e_avail_mwh: float = 80.0,
              price_valley: float = PRICE_VALLEY,
              price_peak: float = PRICE_PEAK,
              eta_chg: float = 0.95, eta_dis: float = 0.95) -> dict:
    """一充一放：谷段充 e_avail，峰段放尽。返回收益明细（元）。"""
    return _calc(e_avail_mwh, price_valley, price_peak, eta_chg, eta_dis)


def two_cycle(e_avail_mwh: float = 80.0,
              price_valley: float = PRICE_VALLEY,
              price_flat: float = PRICE_FLAT,
              price_peak: float = PRICE_PEAK,
              eta_chg: float = 0.95, eta_dis: float = 0.95) -> dict:
    """两充两放：谷充→峰放，平充→峰放。返回两段合计收益（元）。"""
    first = _calc(e_avail_mwh, price_valley, price_peak, eta_chg, eta_dis)
    second = _calc(e_avail_mwh, price_flat, price_peak, eta_chg, eta_dis)
    return dict(
        first=first, second=second,
        profit=first["profit"] + second["profit"],
        revenue=first["revenue"] + second["revenue"],
        cost=first["cost"] + second["cost"],
    )
# @AI_GENERATED: end