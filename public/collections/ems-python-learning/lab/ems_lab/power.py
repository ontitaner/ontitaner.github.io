"""第 02 章：功率、电量与 P/Q/S 计算。

约定：P 单位 kW，Q 单位 kvar，S 单位 kVA，时间单位 s，电量单位 kWh。
"""
from __future__ import annotations

import math
from typing import Sequence


def apparent_power(p_kw: float, q_kvar: float) -> float:
    """视在功率 S = √(P² + Q²)。设备（PCS、变压器）的容量按 S 标定。"""
    return math.hypot(p_kw, q_kvar)


def power_factor(p_kw: float, q_kvar: float) -> float:
    """功率因数幅值 PF = |P| / S，范围 0~1。

    注意：它丢失了“超前/滞后”方向信息，方向要看 Q 的正负（第 17 章）。
    P、Q 都为 0 时没有物理意义，这里按惯例返回 1.0。
    """
    s = apparent_power(p_kw, q_kvar)
    return 1.0 if s == 0 else abs(p_kw) / s


def max_active_power(s_rated_kva: float, q_kvar: float) -> float:
    """给定无功需求 Q 时，设备还能输出的最大有功幅值 √(S² − Q²)。"""
    if s_rated_kva < 0:
        raise ValueError("视在容量必须非负")
    if abs(q_kvar) > s_rated_kva:
        raise ValueError(f"无功需求 {q_kvar} kvar 已超过视在容量 {s_rated_kva} kVA")
    return math.sqrt(s_rated_kva**2 - q_kvar**2)


def max_reactive_power(s_rated_kva: float, p_kw: float) -> float:
    """给定有功 P 时，设备还能输出的最大无功幅值 √(S² − P²)。"""
    if s_rated_kva < 0:
        raise ValueError("视在容量必须非负")
    if abs(p_kw) > s_rated_kva:
        raise ValueError(f"有功 {p_kw} kW 已超过视在容量 {s_rated_kva} kVA")
    return math.sqrt(s_rated_kva**2 - p_kw**2)


def energy_kwh_trapezoid(times_s: Sequence[float], powers_kw: Sequence[float]) -> float:
    """按时间戳做梯形积分，得到电量 kWh。

    采样间隔可以不均匀；时间戳必须严格递增（倒退说明数据有问题）。
    """
    if len(times_s) != len(powers_kw):
        raise ValueError("时间和功率序列长度不一致")
    energy_kws = 0.0
    for i in range(1, len(times_s)):
        dt = times_s[i] - times_s[i - 1]
        if dt <= 0:
            raise ValueError(f"时间戳未递增：索引 {i}")
        energy_kws += (powers_kw[i] + powers_kw[i - 1]) / 2.0 * dt
    return energy_kws / 3600.0  # kW·s → kWh


def pcc_injection_kw(
    p_bess_kw: float,
    p_load_kw: float,
    p_aux_kw: float = 0.0,
    p_loss_kw: float = 0.0,
    p_pv_kw: float = 0.0,
) -> float:
    """站点功率平衡：并网点注入功率 = 所有“发出” − 所有“消耗”。

    结果 > 0：向电网送电（倒送）；< 0：从电网取电。
    """
    return p_pv_kw + p_bess_kw - p_load_kw - p_aux_kw - p_loss_kw

