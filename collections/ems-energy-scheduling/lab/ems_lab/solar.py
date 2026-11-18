# @AI_GENERATED
"""光伏出力曲线与功率平滑

对应章节：03 光储协同
"""
from __future__ import annotations
import math


def pv_curve(t_hour: float, peak_mw: float = 30.0) -> float:
    """简化日光伏曲线：6:00~18:00 半正弦，其余为 0（MW）。"""
    if 6.0 <= t_hour <= 18.0:
        return peak_mw * math.sin(math.pi * (t_hour - 6.0) / 12.0)
    return 0.0


def moving_average(series: list, window: int) -> list:
    """滑动平均（窗口内等权），返回与原序列等长的列表。"""
    out = []
    half = window // 2
    n = len(series)
    for i in range(n):
        lo = max(0, i - half)
        hi = min(n, i + half + 1)
        out.append(sum(series[lo:hi]) / (hi - lo))
    return out


def bess_for_smoothing(pv_series: list, window: int) -> list:
    """储能补偿功率 = 平滑后 − 原始（正值放电、负值充电，MW）。"""
    smooth = moving_average(pv_series, window)
    return [s - p for s, p in zip(smooth, pv_series)]


def track_error(planned: list, actual: list) -> list:
    """计划跟踪误差 = actual - planned（MW，正值表示实际超出计划）。"""
    return [a - p for a, p in zip(actual, planned)]
# @AI_GENERATED: end