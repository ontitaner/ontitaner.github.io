# @AI_GENERATED
"""收益复盘与偏差归因

对应章节：09 经济性后评估

教学示例（对齐 09.3）：
  计划利润 61726 元，实际利润 46526 元，偏差 −15200 元
  = 电价误差 −11800 元 + 可用能量不足 −3400 元（残差 0）。
"""
from __future__ import annotations


def net_profit(revenue: float, cost: float, degradation: float) -> float:
    """净收益 = 收入 − 成本 − 退化成本（元）。"""
    return revenue - cost - degradation


def attribution(planned_profit: float, actual_profit: float, factors: dict) -> dict:
    """偏差归因：factors 为 {因素名: 造成的利润偏差（元）}。

    返回含残差的归因结果，残差 = 总偏差 − 已解释偏差。
    """
    gap = actual_profit - planned_profit
    explained = sum(factors.values())
    residual = gap - explained
    return dict(
        factors=factors, gap=gap, explained=explained,
        residual=residual, check=abs(residual) < 1e-6,
    )
# @AI_GENERATED: end