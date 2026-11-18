# @AI_GENERATED
"""现货市场报价决策

对应章节：07 现货市场

教学示例（对齐 07.3）：
  放电成本（机会成本/LCOS）= 450 元/MWh，预测 LMP = 600 元/MWh。
"""
from __future__ import annotations


def should_discharge(forecast_lmp: float, cost_per_mwh: float) -> bool:
    """预测价高于放电成本才放电。"""
    return forecast_lmp > cost_per_mwh


def bid_price(cost_per_mwh: float, forecast_lmp: float, margin: float = 0.1) -> float:
    """报价（元/MWh）= max(成本, 预测价 × (1 + margin))。"""
    return max(cost_per_mwh, forecast_lmp * (1.0 + margin))
# @AI_GENERATED: end