# @AI_GENERATED
"""第 04 章核心模块：电压源特性与弱电网稳定性。

约定（对齐 00.6 / 01.5 / 02.5 / 04.x 手算）：
- Q-V 下垂反读（电压支撑）：Q = Q_ref + (V_ref − V)/k_q，即 02.5 的 V = V_ref − k_q·(Q − Q_ref) 反解。
- 电压-无功敏感度：ΔV ≈ ΔQ·X_g = ΔQ/SCR（Q 以发出为正，增发无功抬升电压）。
  与 01.5 相量图对称：01.5 是有功电流推相位 Δθ ≈ Δi_d·X_g，本节是无功功率推幅值 ΔV ≈ ΔQ·X_g。
- 多机均流：同一母线电压下，无功按 k_q 反比分配，Q1/Q2 = k_q2/k_q1。
- 环流：两台电压源幅值差 dv → 无功环流 I_circ = dv/(X_s1 + X_s2)。

教学示例默认值（对齐 04.x 手算，主线 50 MW/100 MWh、S_n=50 MVA）：
- V_ref=1.0、k_q=0.05、Q_ref=0；电压跌 0.02 pu → 增发 0.4 pu = 20 Mvar
- SCR=1.8（X_g≈0.556 pu）→ ΔQ=0.2 pu → ΔV≈0.111 pu；强电网 SCR=3（X_g≈0.333 pu）→ ΔV≈0.067 pu（1.67 倍）
- k_q1=0.05、k_q2=0.10、总无功 0.3 pu → Q1=0.2 pu / Q2=0.1 pu（2:1）
- 幅值差 0.02 pu、X_s1=X_s2=0.1 pu → 环流 0.1 pu = 5 Mvar
"""
from __future__ import annotations


def q_from_voltage(v: float, v_ref: float = 1.0, k_q: float = 0.05, q_ref: float = 0.0) -> float:
    """Q-V 下垂反读：并网点电压 v → 自动增发无功 Q。

    Q = Q_ref + (V_ref − V)/k_q（对齐 02.5 的 V = V_ref − k_q·(Q − Q_ref) 反解）。
    电压低于 V_ref 时 Q>0（增发无功顶电压），高于 V_ref 时 Q<0（吸收）。
    """
    if k_q <= 0:
        raise ValueError(f"k_q 必须为正（下垂斜率），实际 {k_q}")
    return q_ref + (v_ref - v) / k_q


def voltage_deviation_pu(dq_pu: float, scr: float) -> float:
    """弱电网电压-无功敏感度：ΔV(pu) = ΔQ·X_g = ΔQ/SCR。

    Q 以发出为正；增发无功（dq_pu>0）抬升并网点电压。
    """
    if scr <= 0:
        raise ValueError(f"SCR 必须为正，实际 {scr}")
    return dq_pu / scr


def share_q(q_total: float, k_q1: float, k_q2: float) -> tuple[float, float]:
    """多机均流：同一母线电压下，无功按 k_q 反比分配。

    Q1/Q2 = k_q2/k_q1，且 Q1 + Q2 = q_total。返回 (q1, q2)。
    """
    if k_q1 <= 0 or k_q2 <= 0:
        raise ValueError(f"k_q 必须为正（下垂斜率），实际 k_q1={k_q1}, k_q2={k_q2}")
    q1 = q_total * k_q2 / (k_q1 + k_q2)
    q2 = q_total * k_q1 / (k_q1 + k_q2)
    return q1, q2


def circ_current_pu(dv: float, xs1: float, xs2: float) -> float:
    """无功环流 I_circ(pu) = dv/(xs1 + xs2)。

    dv 为两台电压源的幅值差，xs1/xs2 为各自设备侧等值感抗。
    """
    denom = xs1 + xs2
    if denom <= 0:
        raise ValueError(f"等值感抗之和必须为正，实际 {denom}")
    return dv / denom
# @AI_GENERATED: end