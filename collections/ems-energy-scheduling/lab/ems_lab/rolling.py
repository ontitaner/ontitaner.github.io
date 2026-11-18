# @AI_GENERATED
"""日内滚动修正与预测误差影响

对应章节：06 日内滚动修正

教学示例（对齐 06.3）：
  三个候选放电时段 [谷, A(平), B(峰)]，日前预测价 [350, 700, 1200]，
  实际价 [350, 1300, 1200]（A 段意外涨过峰段）。
  固定计划：谷充→B 放；滚动重排：谷充→A 放，改善 7600 元。

约定（附录B）：电价元/MWh，能量 MWh。
"""
from __future__ import annotations


def _best_pair(prices: list) -> tuple:
    """返回 (买小时, 卖小时, 买价, 卖价)：最低价买、最高价卖。"""
    buy = min(range(len(prices)), key=lambda i: prices[i])
    sell = max(range(len(prices)), key=lambda i: prices[i])
    return buy, sell, prices[buy], prices[sell]


def arbitrage_profit(prices: list, e_avail: float = 80.0,
                     eta_chg: float = 0.95, eta_dis: float = 0.95) -> float:
    """理想排程（预知价格）的一充一放收益（元）。"""
    _, _, buy_p, sell_p = _best_pair(prices)
    e_grid = e_avail / eta_chg
    e_out = e_avail * eta_dis
    return e_out * sell_p - e_grid * buy_p


def fixed_plan_profit(forecast: list, actual: list, e_avail: float = 80.0,
                      eta_chg: float = 0.95, eta_dis: float = 0.95) -> float:
    """固定计划：用 forecast 选买/卖时段，按 actual 结算的收益（元）。"""
    buy_h, sell_h, _, _ = _best_pair(forecast)
    e_grid = e_avail / eta_chg
    e_out = e_avail * eta_dis
    return e_out * actual[sell_h] - e_grid * actual[buy_h]


def mape(forecast: list, actual: list) -> float:
    """平均绝对百分比误差（%，无量纲百分数，如 5.0 表示 5%）。

    实际值为 0 的点无法计算百分比（分母为 0），跳过；分母按有效点数计。
    """
    total = 0.0
    count = 0
    for f, a in zip(forecast, actual):
        if a != 0.0:
            total += abs((a - f) / a)
            count += 1
    if count == 0:
        return 0.0
    return total / count * 100.0
# @AI_GENERATED: end