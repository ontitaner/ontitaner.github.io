# @AI_GENERATED
"""AVC 月度考核评分与结算模型

对应章节：07 AVC考核与结算模型

教学示例默认值（对齐 07.4 手算）：
  W_v=0.5, W_a=0.3, W_q=0.2（典型权重）
  VQR=97%, 投运率=98.7%, 响应时间均值=22s
  容量补偿：Q_rated=20 Mvar, 结算电价=10 元/(Mvar·h)
  S_month = 90.0×0.5 + 100×0.3 + 76.7×0.2 = 86.9
"""
from __future__ import annotations


def s_voltage(vqr: float, vqr_target: float = 0.99) -> float:
    if vqr >= vqr_target:
        return 100.0
    return max(0.0, 100.0 - (vqr_target - vqr) * 500.0)


def s_availability(availability: float) -> float:
    if availability >= 0.98:
        return 100.0
    elif availability >= 0.90:
        return (availability - 0.90) / 0.08 * 100.0
    else:
        return 0.0


def s_performance(t_avg_s: float, t_target_s: float = 15.0) -> float:
    if t_avg_s <= t_target_s:
        return 100.0
    return max(0.0, 100.0 - (t_avg_s - t_target_s) / t_target_s * 50.0)


def monthly_score(
    vqr: float,
    availability: float,
    t_avg_s: float,
    w_v: float = 0.5,
    w_a: float = 0.3,
    w_q: float = 0.2,
) -> float:
    sv = s_voltage(vqr)
    sa = s_availability(availability)
    sq = s_performance(t_avg_s)
    return sv * w_v + sa * w_a + sq * w_q


def capacity_compensation(
    q_rated_mvar: float,
    hours: float,
    price_per_mvarh: float,
    score_ratio: float,
    penalty_coef: float = 1.0,
) -> float:
    base = q_rated_mvar * hours * price_per_mvarh
    return base * score_ratio * penalty_coef
# @AI_GENERATED: end