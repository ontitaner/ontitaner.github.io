# @AI_GENERATED
"""第 07 章核心模块：构网型并网测试与验收。

验收 = 把第 06 章状态机的每一次迁移，落成可判定的试验项，并给每项试验配上
跨设备时标对齐的证据链。本模块不重复定义前序公式，只复用 03/05 章纯函数做
「验收指标计算 + 合格判定 + 证据链」三层封装。

五项验收（对齐 02/03/05/06 手算）：
1. 惯量响应：制造功率缺口 ΔP → 测 RoCoF → 反推等效惯量 J_eq = f_n·ΔP/RoCoF，
   判定 J_eq ≥ 合同要求（03.2 的 20 s）。
2. 一次调频：频率阶跃 Δf → 构网无死区增发 ΔP = −D·Δf/f_n，与传统死区对比。
3. 并网冲击：预同步后 ΔV/Δθ → 冲击电流 I = ΔV/X_s、I = V·Δθ/X_s，判定 ≤ I_max。
4. 黑启动带载：每批无功阶跃 ΔQ → 电压跌落 ΔV = ΔQ·X_s，判定 ≤ ΔV_max。
5. 证据链：跨设备（调度/EMS/PCS 录波）同一事件时标对齐，判定偏差 ≤ 阈值。

教学示例默认值（主线 50 MW/100 MWh、S_n=50 MVA、SCR≈1.8）：
- 惯量：ΔP=0.1 pu、改造后 RoCoF=0.25 Hz/s → J_eq=20 s（≥ 合同 20 s 达标）；
  改造前 RoCoF=0.75 Hz/s → J_eq≈6.667 s（不达标）。
- 一次调频：Δf=−0.6 Hz、D=33.333 pu（δ=3%）→ 增发 0.4 pu=20 MW；
  传统死区 ±0.06 Hz 仅 0.36 pu=18 MW；Δf=−0.04 Hz 死区内传统为 0。
- 并网冲击：Δθ=0.01 rad、ΔV=0.01 pu、X_s=0.1 → 各 0.1 pu（= I_max 达标）；
  未预同步 Δθ=0.1 rad → 1.0 pu（越限）；幅值差 0.02 pu → 0.2 pu（越限）。
- 黑启动：ΔV_max=0.05 pu、X_s=0.1 → 单次最大无功阶跃 0.5 pu；
  一次带 0.6 pu → 跌落 0.06 pu（越限）。
- 证据链：跨设备时钟偏差 ≤ 10 ms 达标。
"""
from __future__ import annotations

from dataclasses import dataclass

from .grid_switch import (
    inrush_from_amplitude,
    inrush_from_phase,
    voltage_drop_pu,
)
from .inertia import (
    gridforming_delta_p_pu,
    pfr_delta_p_pu,
    system_inertia_s,
)


@dataclass(frozen=True)
class AcceptanceCriteria:
    """构网型并网验收判据（教学示例，非整定值）。"""

    delta_p_pu: float = 0.1        # 惯量试验功率缺口（0.1 pu = 5 MW）
    j_eq_req_s: float = 20.0       # 合同要求等效惯量（03.2 总 20 s）
    pfr_df_hz: float = -0.6        # 一次调频试验频率阶跃（负 = 跌落）
    pfr_d: float = 33.333          # 一次调频试验 D（δ=3%）
    pfr_db_hz: float = 0.06        # 传统一次调频死区
    pfr_tol_pu: float = 0.02       # 一次调频允许偏差（pu）
    i_max: float = 0.1             # 允许最大并网冲击电流（pu）
    xs: float = 0.1                # 设备侧等值感抗（pu）
    dv_max: float = 0.05           # 黑启动允许最大电压跌落（pu）
    ts_bias_max_ms: float = 10.0   # 证据链时钟偏差上限（ms）


# ---------- 试验 1：惯量响应 ----------

def measure_rocof_hz(df_hz: float, dt_s: float) -> float:
    """由频率变化窗口反推 RoCoF 跌速大小（Hz/s）：RoCoF = |Δf| / Δt。

    00.1 场景：频率 0.8 s 内跌 0.6 Hz → 0.6 / 0.8 = 0.75 Hz/s。
    """
    if dt_s <= 0:
        raise ValueError(f"窗口时长必须为正，实际 {dt_s}")
    return abs(df_hz) / dt_s


def inertia_acceptance(delta_p_pu: float, rocof_hz: float,
                       criteria: AcceptanceCriteria | None = None) -> tuple[bool, float]:
    """惯量响应验收：反推等效惯量 J_eq = f_n·ΔP/RoCoF，判定 J_eq ≥ 合同要求。

    返回 (是否合格, J_eq)。改造后 RoCoF=0.25 → J_eq=20 s 达标；
    改造前 RoCoF=0.75 → J_eq≈6.667 s 不达标。
    """
    crit = criteria or AcceptanceCriteria()
    if rocof_hz == 0:
        raise ValueError("RoCoF 不能为 0（无法反求惯量）")
    j_eq = system_inertia_s(delta_p_pu, rocof_hz)
    return j_eq >= crit.j_eq_req_s, j_eq


# ---------- 试验 2：一次调频 ----------

def pfr_gridforming_pu(df_hz: float, D: float, f_n: float = 50.0) -> float:
    """构网型无死区一次调频增发（pu）：ΔP = −D·Δf/f_n。Δf<0（跌落）→ 正（增发）。"""
    return gridforming_delta_p_pu(df_hz, D, f_n)


def pfr_traditional_pu(df_hz: float, D: float, db_hz: float = 0.06, f_n: float = 50.0) -> float:
    """传统有死区一次调频增发（pu）：ΔP = −D·deadzone(Δf)/f_n。死区内为 0。"""
    return pfr_delta_p_pu(df_hz, D, db_hz, f_n)


def pfr_acceptance(df_hz: float, D: float, expected_pu: float,
                   tol_pu: float = 0.02, f_n: float = 50.0) -> tuple[bool, float]:
    """一次调频验收：构网无死区增发 ΔP = −D·Δf/f_n，判定与期望值偏差 ≤ tol。

    返回 (是否合格, 实测增发 pu)。Δf=−0.6、D=33.333 → 实测 0.4 pu（=20 MW）。
    """
    measured = gridforming_delta_p_pu(df_hz, D, f_n)
    return abs(measured - expected_pu) <= tol_pu, measured


# ---------- 试验 3：并网冲击 ----------

def inrush_components(dv_pu: float, dtheta_rad: float, v: float = 1.0, xs: float = 0.1) -> tuple[float, float]:
    """并网冲击两分量：(幅值差冲击 I_amp, 相位差冲击 I_ph)（pu）。"""
    return inrush_from_amplitude(dv_pu, xs), inrush_from_phase(dtheta_rad, v, xs)


def inrush_pass(i_pu: float, i_max: float = 0.1) -> bool:
    """并网冲击验收判定：冲击电流 ≤ I_max 即合格。"""
    return i_pu <= i_max


# ---------- 试验 4：黑启动带载 ----------

def blackstart_acceptance(dq_pu: float, criteria: AcceptanceCriteria | None = None) -> tuple[bool, float]:
    """黑启动带载验收：单次无功阶跃 ΔQ 的电压跌落 ΔV = ΔQ·X_s ≤ ΔV_max？

    返回 (是否合格, ΔV)。ΔV_max=0.05、X_s=0.1 → 单次最大 0.5 pu；
    一次带 0.6 pu → 0.06 pu 越限。
    """
    crit = criteria or AcceptanceCriteria()
    dv = voltage_drop_pu(dq_pu, crit.xs)
    return dv <= crit.dv_max, dv


# ---------- 试验 5：证据链时标对齐 ----------

@dataclass(frozen=True)
class EvidenceRecord:
    """单条证据：某设备对某事件的带时标记录。"""

    event: str        # 事件名（如 T_evt / T_start / T_end）
    source: str       # 来源（调度主站 / EMS / PCS 录波）
    t_ms: float       # 时标（相对触发 0 点的 ms）


def clock_bias_ms(t_a_ms: float, t_b_ms: float) -> float:
    """两设备记录同一事件的时标偏差（ms）= |t_a − t_b|。"""
    return abs(t_a_ms - t_b_ms)


def clock_bias_pass(bias_ms: float, max_ms: float = 10.0) -> bool:
    """时钟偏差验收判定：偏差 ≤ max_ms（默认 10 ms）即合格。"""
    return bias_ms <= max_ms


def response_time_ms(t_start_ms: float, t_cmd_ms: float) -> float:
    """响应时间（ms）= T_start − T_cmd（设备开始动作时刻 − 调度触发时刻）。"""
    return t_start_ms - t_cmd_ms


def evidence_chain_pass(records: list[EvidenceRecord], max_bias_ms: float = 10.0) -> tuple[bool, float]:
    """证据链时标对齐验收：同一事件跨设备最大时钟偏差 ≤ max_bias_ms？

    同一事件由多台设备记录，取各设备时标的最大跨度作为该事件的偏差；
    全体事件的最大偏差与阈值比较。返回 (是否合格, 最大偏差 ms)。
    """
    if not records:
        raise ValueError("证据链不能为空")
    by_event: dict[str, list[float]] = {}
    for r in records:
        by_event.setdefault(r.event, []).append(r.t_ms)
    max_bias = 0.0
    for times in by_event.values():
        if len(times) >= 2:
            max_bias = max(max_bias, max(times) - min(times))
    return max_bias <= max_bias_ms, max_bias
# @AI_GENERATED: end