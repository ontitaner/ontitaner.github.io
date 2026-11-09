# @AI_GENERATED
"""最大需量与储能削峰

对应章节：02 需量管理

需量按 15 min 平均功率计（输入序列即 15min 均值）。
"""
from __future__ import annotations


def peak_demand(load_mw: list) -> float:
    """需量 = 15 min 平均功率序列的最大值（MW）。"""
    return max(load_mw)


def demand_charge(peak_mw: float, price_per_kw_month: float = 40.0) -> float:
    """需量电费（元/月）= 最大需量(MW) × 1000 × 单价(元/kW·月)。"""
    return peak_mw * 1000.0 * price_per_kw_month


def shave(load_mw: list, p_bess_max: float, target_demand: float) -> list:
    """储能削峰：返回各时点放电功率（MW，非负），使削峰后需量尽量 ≤ target。"""
    out = []
    for load in load_mw:
        excess = load - target_demand
        out.append(min(p_bess_max, max(0.0, excess)))
    return out


def shaved_peak(load_mw: list, bess_discharge: list) -> float:
    """削峰后的最大需量 = max(load - bess)（MW）。"""
    return max(max(0.0, l - b) for l, b in zip(load_mw, bess_discharge))
# @AI_GENERATED: end