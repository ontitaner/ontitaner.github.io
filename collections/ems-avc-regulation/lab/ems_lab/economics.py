# @AI_GENERATED
"""SVG vs 储能无功全寿命经济决策

对应章节：07b 无功经济性决策

教学示例默认值（对齐 07b.2~07b.4 手算）：
  S=50 MVA, H=4000h, ΔP=0.5 元/kWh, η=0.9
  SVG 初投 180 万, 10 年运维 50 万, 全寿命 230 万
  PCS 年损失 180 万（Q_avg=10 Mvar）, 10 年 1800 万
  SVG 年化 23 万, ROI > 20 倍, 盈亏 Q_avg≈3.6 Mvar
"""
from __future__ import annotations


def pcs_opportunity_cost(
    q_avg_mvar: float,
    s_nominal_mva: float = 50.0,
    hours_per_year: float = 4000.0,
    price_spread_yuan_per_kwh: float = 0.5,
    efficiency: float = 0.9,
    years: int = 10,
) -> dict:
    p_displaced_mw = q_avg_mvar ** 2 / (2.0 * s_nominal_mva)
    annual_loss_kwh = p_displaced_mw * hours_per_year * 1000.0
    annual_loss_yuan = annual_loss_kwh * price_spread_yuan_per_kwh * efficiency
    total_loss_yuan = annual_loss_yuan * years
    return {
        'p_displaced_mw': p_displaced_mw,
        'annual_loss_yuan': annual_loss_yuan,
        'annual_loss_wan': annual_loss_yuan / 10000.0,
        'total_loss_yuan': total_loss_yuan,
        'total_loss_wan': total_loss_yuan / 10000.0,
    }


def svg_lifecycle_cost(
    initial_invest_wan: float = 180.0,
    annual_maintenance_wan: float = 5.0,
    years: int = 10,
) -> dict:
    total_maintenance = annual_maintenance_wan * years
    total_wan = initial_invest_wan + total_maintenance
    annualized_wan = total_wan / years
    return {
        'initial_invest_wan': initial_invest_wan,
        'total_maintenance_wan': total_maintenance,
        'total_wan': total_wan,
        'annualized_wan': annualized_wan,
    }


def breakeven_q(
    s_nominal_mva: float = 50.0,
    hours_per_year: float = 4000.0,
    price_spread_yuan_per_kwh: float = 0.5,
    efficiency: float = 0.9,
    svg_annual_wan: float = 23.0,
) -> float:
    import math
    return math.sqrt(
        2.0
        * s_nominal_mva
        * svg_annual_wan
        * 10000.0
        / (hours_per_year * 1000.0 * price_spread_yuan_per_kwh * efficiency)
    )


def svg_roi(q_avg_mvar: float = 10.0) -> dict:
    svg_cost = svg_lifecycle_cost()
    pcs_cost = pcs_opportunity_cost(q_avg_mvar)
    saved_wan = pcs_cost['total_loss_wan']
    invested_wan = svg_cost['total_wan']
    roi = saved_wan / invested_wan if invested_wan > 0 else float('inf')
    return {
        'svg_total_wan': invested_wan,
        'pcs_loss_wan': saved_wan,
        'roi': roi,
        'svg_annual_wan': svg_cost['annualized_wan'],
        'pcs_annual_wan': pcs_cost['annual_loss_wan'],
        'breakeven_q_mvar': breakeven_q(svg_annual_wan=svg_cost['annualized_wan']),
    }
# @AI_GENERATED: end