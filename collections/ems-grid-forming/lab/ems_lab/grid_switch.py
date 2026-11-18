# @AI_GENERATED
"""第 05 章核心模块：并离网切换与黑启动。

约定（对齐 00.6 / 04.5 / 05.x 手算）：
- 并网冲击电流：构网型自建电压源与电网通过设备侧等值感抗 X_s 相连，并网瞬间的
  电压差 ΔU 产生冲击电流 I_inrush = ΔU/X_s。
  · 幅值差 ΔV → ΔU = ΔV
  · 相位差 Δθ → ΔU ≈ V·Δθ（小角度 sinΔθ≈Δθ）
- 预同步：把幅值差/相位差压进阈值，使并网冲击 ≤ I_max。阈值反推：
  ΔV_max = I_max·X_s；Δθ_max = I_max·X_s/V。
- 预同步追赶时长：调频 Δf 追赶相位，角速度 ω_slip = 2π·Δf，t = Δθ0/(2π·Δf)。
- 解列功率回零：以爬坡速率 ramp 把并网交换功率降到 0，t = P/ramp。
- 黑启动带载：每批带载的**无功阶跃 ΔQ** 在 X_s 上产生电压跌落 ΔV ≈ ΔQ·X_s
  （对齐 04.3「无功推幅值」；黑启动无电网，只由设备侧 X_s 决定）；
  单次最大无功阶跃 ΔQ_max = ΔV_max/X_s。

教学示例默认值（对齐 05.x 手算，主线 50 MW/100 MWh、S_n=50 MVA）：
- X_s=0.1 pu、允许最大冲击 I_max=0.1 pu → ΔV_max=0.01 pu、Δθ_max=0.01 rad≈0.57°
- 未预同步 Δθ=0.1 rad（5.7°）→ 冲击 1.0 pu；预同步达标 Δθ=0.01 rad → 冲击 0.1 pu
- 幅值差 0.02 pu → 冲击 0.2 pu
- 预同步：Δθ0=0.1 rad、Δf=0.05 Hz → t≈0.318 s
- 解列：P=0.2 pu、爬坡 0.5 pu/s → 回零 0.4 s
- 黑启动：X_s=0.1 pu、允许跌落 0.05 pu → 单次最大无功阶跃 0.5 pu；一次带 0.6 pu → 跌落 0.06 pu（越限）
"""
from __future__ import annotations

import math


def inrush_from_amplitude(dv_pu: float, xs: float = 0.1) -> float:
    """幅值差 → 并网冲击电流：I = ΔV/X_s（pu）。

    dv_pu 为并网瞬间两电压源的幅值差（pu），xs 为设备侧等值感抗（pu）。
    """
    if xs <= 0:
        raise ValueError(f"设备侧等值感抗必须为正，实际 {xs}")
    return dv_pu / xs


def inrush_from_phase(dtheta_rad: float, v: float = 1.0, xs: float = 0.1) -> float:
    """相位差 → 并网冲击电流：I = V·Δθ/X_s（pu）。

    小角度近似 sinΔθ≈Δθ，dtheta_rad 为并网瞬间相位差（rad）。
    """
    if xs <= 0:
        raise ValueError(f"设备侧等值感抗必须为正，实际 {xs}")
    if v <= 0:
        raise ValueError(f"电压幅值必须为正，实际 {v}")
    return v * dtheta_rad / xs


def amplitude_threshold_pu(i_max: float = 0.1, xs: float = 0.1) -> float:
    """幅值差阈值：ΔV_max = I_max·X_s（pu）。

    由允许最大冲击电流 I_max 反推并网前允许的幅值差。
    """
    if xs <= 0:
        raise ValueError(f"设备侧等值感抗必须为正，实际 {xs}")
    return i_max * xs


def phase_threshold_rad(i_max: float = 0.1, xs: float = 0.1, v: float = 1.0) -> float:
    """相位差阈值：Δθ_max = I_max·X_s/V（rad）。

    由允许最大冲击电流 I_max 反推并网前允许的相位差。
    """
    if xs <= 0:
        raise ValueError(f"设备侧等值感抗必须为正，实际 {xs}")
    if v <= 0:
        raise ValueError(f"电压幅值必须为正，实际 {v}")
    return i_max * xs / v


def pre_sync_time(dtheta0_rad: float, df_hz: float) -> float:
    """预同步追赶时长：t = |Δθ0|/(2π·|Δf|)（s）。

    调频 Δf 追赶相位，追赶角速度 ω_slip = 2π·Δf；时长取绝对值保证对称。
    """
    if df_hz == 0:
        raise ValueError("调频量 Δf 不能为 0（无法追赶相位）")
    return abs(dtheta0_rad) / (2.0 * math.pi * abs(df_hz))


def unload_time(p_pu: float, ramp_pu_s: float = 0.5) -> float:
    """解列功率回零时长：t = P/ramp（s）。

    p_pu 为解列前并网交换功率（pu），ramp_pu_s 为功率爬坡速率（pu/s）。
    """
    if p_pu < 0:
        raise ValueError(f"解列前功率不能为负，实际 {p_pu}")
    if ramp_pu_s <= 0:
        raise ValueError(f"爬坡速率必须为正，实际 {ramp_pu_s}")
    return p_pu / ramp_pu_s


def voltage_drop_pu(dq_pu: float, xs: float = 0.1) -> float:
    """黑启动带载电压跌落：ΔV ≈ ΔQ·X_s（pu）。

    dq_pu 为单次带载的无功阶跃（pu），xs 为设备侧等值感抗（pu）。
    """
    if xs <= 0:
        raise ValueError(f"设备侧等值感抗必须为正，实际 {xs}")
    return dq_pu * xs


def max_load_step_pu(dv_max: float = 0.05, xs: float = 0.1) -> float:
    """单次最大无功阶跃：ΔQ_max = ΔV_max/X_s（pu）。

    由允许最大电压跌落 ΔV_max 反推黑启动时单次允许带载的无功阶跃。
    """
    if xs <= 0:
        raise ValueError(f"设备侧等值感抗必须为正，实际 {xs}")
    return dv_max / xs
# @AI_GENERATED: end