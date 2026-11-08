# @AI_GENERATED
"""电压合格率与响应时间计算

对应章节：04 AVC考核指标与统计口径

教学示例默认值（对齐 04.3 手算）：
  U_target=116.0 kV, deadband=±0.5 kV, 合格范围=±0.5 kV
  24h 分钟级数据，23:15 越限 5min → VQR=99.65%
"""
from __future__ import annotations
from typing import List


def voltage_qualification_rate(
    voltage_series: List[float],
    target: float = 116.0,
    band: float = 0.5,
) -> float:
    total = len(voltage_series)
    if total == 0:
        return 0.0
    qualified = sum(
        1 for v in voltage_series
        if target - band <= v <= target + band
    )
    return qualified / total


def response_time_flag(
    t_response_s: float,
    t_target_s: float = 30.0,
) -> tuple[bool, float]:
    qualified = t_response_s <= t_target_s
    excess = max(0.0, t_response_s - t_target_s)
    return qualified, excess
# @AI_GENERATED: end