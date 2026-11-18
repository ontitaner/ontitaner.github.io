# @AI_GENERATED
"""第 06 章核心模块：构网型 EMS 控制链路（五级流水线 + 状态机）。

约定（对齐 01.6 / 02.x / 03.x / 05.x 手算）：
- 五级流水线：采集(Sense) → 校验(Validate) → 决策(Decide) → 下发(Actuate) → 对账(Account)。
  跟网→构网升级时：采集/下发「扩展」、校验「改对象」、决策(状态机)「重写」、对账「重写」。
- 参数一致性校验对象切换：跟网型校验死区 db / 调差率 δ% / 限幅 P_lim；
  构网型校验 J / D / V_ref（J>0、D>0 且折算调差率 δ%=100/D 在限幅内、V_ref 在幅值限幅内）。
- 并离网状态机三状态：并网运行(下垂/VSG)、离网运行(V/f)、黑启动(V/f+分批带载)；
  迁移门槛复用 05 章 grid_switch 的时序门（功率回零、分闸延时、预同步、切换窗口）。

教学示例默认值（对齐 02/03/05 手算，主线 50 MW/100 MWh、S_n=50 MVA）：
- 构网三参数：J=4.0 s、D=20 pu（折算 δ=5%）、V_ref=1.0 pu
- 校验限幅：J>0；D>0 且 δ%=100/D ∈ [1,10]；V_ref ∈ [0.9,1.1] pu
- 状态机时序：并网→离网 解列 0.5 s（回零 0.4 s + 延时 0.1 s）；
  离网→并网 再并网 0.92 s（预同步 0.318 s + 切换窗口 0.2 s + 功率转移 0.4 s）
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .grid_switch import pre_sync_time, unload_time
from .inertia import D_to_droop_pct


class GridMode(Enum):
    """并离网状态机的三种运行模式。"""

    ON_GRID = "并网运行"    # 下垂/VSG，参与系统调频调压
    ISLAND = "离网运行"     # V/f 控制，自建并维持孤岛电压频率
    BLACK_START = "黑启动"  # V/f 控制 + 分批带载（先恒阻抗后电机）


# 状态机事件（迁移条件）
EV_UNLOAD = "转入离网"    # 调度指令：并网 → 离网
EV_RESYNC = "再并网"      # 电网恢复：离网 → 并网
EV_BLACKOUT = "电网全黑"  # 失电：任意并网状态 → 黑启动
EV_LOADED = "带载完成"    # 黑启动完成：黑启动 → 离网


@dataclass(frozen=True)
class VsgLimits:
    """构网三参数校验限幅（教学示例，非整定值）。"""

    j_min: float = 0.0          # J 必须 > 0
    d_min: float = 0.0          # D 必须 > 0
    droop_pct_min: float = 1.0  # D 折算调差率下限 δ% ≥ 1
    droop_pct_max: float = 10.0  # D 折算调差率上限 δ% ≤ 10
    v_ref_min: float = 0.9      # V_ref 下限（pu）
    v_ref_max: float = 1.1      # V_ref 上限（pu）


def validate_vsg_params(J: float, D: float, v_ref: float, limits: VsgLimits | None = None) -> list[str]:
    """校验构网三参数 J/D/V_ref，返回错误列表（空列表 = 全部合法）。

    - J > 0：虚拟惯量必须为正，J=0 等于退回无惯量电流源；
    - D > 0 且 δ%=100/D ∈ [δ_min, δ_max]：阻尼必须为正且对应调差率在合理范围；
    - v_ref ∈ [v_ref_min, v_ref_max]：自建电压幅值不能偏离额定太远（否则并网冲击超限）。
    """
    limits = limits or VsgLimits()
    errors: list[str] = []
    if J <= limits.j_min:
        errors.append(f"J 必须为正（虚拟惯量），实际 {J}（J=0 退回无惯量）")
    if D <= limits.d_min:
        errors.append(f"D 必须为正（阻尼），实际 {D}（D=0 无阻尼会振荡）")
    else:
        droop = D_to_droop_pct(D)
        if not (limits.droop_pct_min <= droop <= limits.droop_pct_max):
            errors.append(f"D 折算调差率 {droop:.1f}% 超限（应 {limits.droop_pct_min:.0f}~{limits.droop_pct_max:.0f}%）")
    if not (limits.v_ref_min <= v_ref <= limits.v_ref_max):
        errors.append(f"V_ref 超限，实际 {v_ref}（应 {limits.v_ref_min}~{limits.v_ref_max} pu）")
    return errors


# 状态机迁移表：{(当前状态, 事件): 下一状态}
_TRANSITIONS: dict[tuple[GridMode, str], GridMode] = {
    (GridMode.ON_GRID, EV_UNLOAD): GridMode.ISLAND,
    (GridMode.ISLAND, EV_RESYNC): GridMode.ON_GRID,
    (GridMode.ON_GRID, EV_BLACKOUT): GridMode.BLACK_START,
    (GridMode.ISLAND, EV_BLACKOUT): GridMode.BLACK_START,
    (GridMode.BLACK_START, EV_LOADED): GridMode.ISLAND,
}


def transition(mode: GridMode, event: str) -> GridMode:
    """状态机迁移：给定当前状态与事件，返回下一状态。

    合法迁移见 _TRANSITIONS；非法迁移（如并网状态下「带载完成」）抛 ValueError。
    """
    key = (mode, event)
    if key not in _TRANSITIONS:
        raise ValueError(f"非法迁移：{mode.value} 状态下不允许事件「{event}」")
    return _TRANSITIONS[key]


def unload_duration_s(p_pu: float = 0.2, ramp_pu_s: float = 0.5, trip_delay_s: float = 0.1) -> float:
    """解列总耗时 = 功率回零时长 + 分闸延时（s）。

    t = P/ramp + delay = 0.2/0.5 + 0.1 = 0.5 s（对齐 05.4 解列门）。
    """
    return unload_time(p_pu, ramp_pu_s) + trip_delay_s


def resync_duration_s(dtheta0_rad: float = 0.1, df_hz: float = 0.05,
                      switch_window_s: float = 0.2, p_transfer_pu: float = 0.2,
                      ramp_pu_s: float = 0.5) -> float:
    """再并网总耗时 = 预同步时长 + 下垂接管窗口 + 功率转移时长（s）。

    t = Δθ0/(2π·Δf) + 窗口 + P/ramp ≈ 0.318 + 0.2 + 0.4 = 0.92 s（对齐 05.4 再并网关）。
    """
    return pre_sync_time(dtheta0_rad, df_hz) + switch_window_s + unload_time(p_transfer_pu, ramp_pu_s)
# @AI_GENERATED: end