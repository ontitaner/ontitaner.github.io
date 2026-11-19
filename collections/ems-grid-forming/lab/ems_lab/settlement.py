# @AI_GENERATED
"""第 08 章核心模块：构网型考核与结算——惯量/阻尼拆分计量 + 结算。

约定（对齐 02.x / 03.x / 08.x 手算，主线 50 MW/100 MWh、S_n=50 MVA）：
- VSG 摇摆方程 J·dω/dt = P_ref − P_e − D·(ω−1) 拆成两项：
  惯量项 P_inertia = J·|RoCoF|/f_n（瞬时顶，只在频率变化时出现）
  阻尼项 P_droop  = D·|Δf|/f_n   （持续供，随频偏持续存在）
- 一次频率跌落事件（08.x 教学示例）：频率 0.6 Hz 以 RoCoF=0.25 Hz/s 跌下，
  跌落段 Δt_drop = Δf/RoCoF = 2.4 s，之后稳定在 Δf=0.6 Hz 持续 T_hold=30 s。
- 惯量支撑电量（MW·s）：W_inertia = J·Δf·S_n/f_n，与 RoCoF、持续时长无关。
- 阻尼电量（MW·s）：W_droop = D·S_n/f_n · [Δf²/(2·RoCoF) + Δf·T_hold]。
- 结算口径：惯量按「容量」结算（元/惯量秒 × J_vsg），阻尼按「电量」结算（元/MWh × W）。

教学示例默认值（对齐 08.x 手算；内部取精确分数 40/3、100/3 使结算金额干净）：
- 惯量：J_vsg=40/3≈13.333 s、RoCoF=0.25、Δf=0.6 → P_inertia=3.333 MW、W_inertia=8 MW·s。
- 阻尼：D=100/3≈33.333 pu（δ=3%）、Δf=0.6、T_hold=30 s → 稳定段 20 MW、
  W_droop=24+600=624 MW·s=0.1733 MWh。
- 结算：c_inertia=300 元/惯量秒 → 4000 元；c_energy=360 元/MWh → 62.4 元。
- 考核：完成率阈值 60%；反向加倍、完成率不足按缺额计费。
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SettlementConfig:
    """构网型考核与结算参数（教学示例值，非整定值）。"""

    sn_mva: float = 50.0        # 站级基准容量（MVA）
    f_n: float = 50.0           # 额定频率（Hz）
    j_vsg: float = 40.0 / 3.0   # 本站虚拟惯量（精确 40/3≈13.333 s，03 章取三位小数）
    d: float = 100.0 / 3.0      # 阻尼（精确 100/3≈33.333 pu，δ=3%）
    df_hz: float = 0.6          # 事件频偏幅值（Hz，正数）
    rocof_hz: float = 0.25      # 跌落阶段 RoCoF（Hz/s）
    t_hold_s: float = 30.0      # 稳定阶段持续时长（s）
    c_inertia: float = 300.0    # 惯量容量单价（元/惯量秒）
    c_energy: float = 360.0     # 电量单价（元/MWh）
    completion_min: float = 0.6 # 完成率下限（60%）

    def __post_init__(self):
        if self.sn_mva <= 0 or self.f_n <= 0:
            raise ValueError("S_n 与 f_n 必须为正")
        if self.j_vsg < 0 or self.d < 0:
            raise ValueError("J_vsg 与 D 不能为负")
        if self.df_hz < 0 or self.rocof_hz <= 0 or self.t_hold_s < 0:
            raise ValueError("Δf/T_hold 不能为负，RoCoF 必须为正")
        if self.c_inertia < 0 or self.c_energy < 0:
            raise ValueError("单价不能为负")
        if not 0.0 < self.completion_min <= 1.0:
            raise ValueError("完成率阈值必须在 (0, 1]")


def inertia_power_mw(j_s: float, rocof_hz: float, cfg: SettlementConfig | None = None) -> float:
    """惯量支撑功率（MW）= J·|RoCoF|/f_n·S_n。只在频率变化（RoCoF≠0）时存在。"""
    c = cfg or SettlementConfig()
    return j_s * abs(rocof_hz) / c.f_n * c.sn_mva


def droop_power_mw(df_hz: float, cfg: SettlementConfig | None = None) -> float:
    """阻尼/一次调频支撑功率（MW）= D·|Δf|/f_n·S_n。随频偏持续存在。"""
    c = cfg or SettlementConfig()
    return c.d * abs(df_hz) / c.f_n * c.sn_mva


def split_power_mw(df_hz: float, rocof_hz: float,
                   cfg: SettlementConfig | None = None) -> tuple[float, float]:
    """把 VSG 出力拆成两项：返回 (惯量功率 MW, 阻尼功率 MW)。"""
    c = cfg or SettlementConfig()
    return inertia_power_mw(c.j_vsg, rocof_hz, c), droop_power_mw(df_hz, c)


def inertia_energy_mws(cfg: SettlementConfig | None = None) -> float:
    """惯量支撑电量（MW·s）= J·Δf·S_n/f_n。

    与 RoCoF、持续时长无关：RoCoF 越大跌得越快，但惯性功率也越大，
    两者的乘积（能量）恒定——惯量只能「吐」出固定的一份动能。
    """
    c = cfg or SettlementConfig()
    return c.j_vsg * c.df_hz * c.sn_mva / c.f_n


def droop_energy_mws(cfg: SettlementConfig | None = None) -> float:
    """阻尼/一次调频电量（MW·s）= 跌落段 + 稳定段。

    跌落段：Δf 从 0 线性涨到 Δf，平均功率 D·(Δf/2)/f_n·S_n，时长 Δf/RoCoF；
    稳定段：Δf 恒定，功率 D·Δf/f_n·S_n，时长 T_hold。
    合式：W_droop = D·S_n/f_n · [Δf²/(2·RoCoF) + Δf·T_hold]，随 T_hold 线性增长。
    """
    c = cfg or SettlementConfig()
    k = c.d * c.sn_mva / c.f_n
    drop = k * (c.df_hz ** 2 / (2.0 * c.rocof_hz))
    hold = k * c.df_hz * c.t_hold_s
    return drop + hold


def mws_to_mwh(mws: float) -> float:
    """MW·s → MWh（除以 3600）。"""
    return mws / 3600.0


def completion_rate(w_actual_mws: float, w_theory_mws: float) -> float:
    """完成率 = 实际积分电量 / 理论积分电量。"""
    if w_theory_mws == 0:
        raise ValueError("理论积分电量不能为 0（无法计算完成率）")
    return w_actual_mws / w_theory_mws


def assess(w_theory_mws: float, w_actual_mws: float,
           completion_min: float = 0.6) -> str:
    """考核判定：反向 → 'reverse'；同向但完成率不足 → 'under'；通过 → 'pass'。"""
    if w_theory_mws == 0:
        raise ValueError("理论积分电量不能为 0")
    if w_theory_mws * w_actual_mws < 0:
        return "reverse"
    if completion_rate(w_actual_mws, w_theory_mws) < completion_min:
        return "under"
    return "pass"


def penalty_fee(w_theory_mws: float, w_actual_mws: float,
                cfg: SettlementConfig | None = None) -> float:
    """考核费用（元）：反向加倍；完成率不足按缺额电量 × 单价计；通过为 0。"""
    c = cfg or SettlementConfig()
    verdict = assess(w_theory_mws, w_actual_mws, c.completion_min)
    if verdict == "reverse":
        return 2.0 * c.c_energy * mws_to_mwh(abs(w_theory_mws))
    if verdict == "under":
        shortage = max(w_theory_mws - w_actual_mws, 0.0)
        return c.c_energy * mws_to_mwh(shortage)
    return 0.0


def settle_inertia(cfg: SettlementConfig | None = None) -> float:
    """惯量按「容量」结算（元）= c_inertia × J_vsg。"""
    c = cfg or SettlementConfig()
    return c.c_inertia * c.j_vsg


def settle_droop(cfg: SettlementConfig | None = None) -> float:
    """阻尼/一次调频按「电量」结算（元）= c_energy × W_droop(MWh)。"""
    c = cfg or SettlementConfig()
    return c.c_energy * mws_to_mwh(droop_energy_mws(c))


def settle_inertia_as_energy(cfg: SettlementConfig | None = None) -> float:
    """错误口径对照：若惯量也按电量结算（元）= c_energy × W_inertia(MWh)。

    用于演示「口径错了惯量这笔钱会凭空消失 3 个数量级」。
    """
    c = cfg or SettlementConfig()
    return c.c_energy * mws_to_mwh(inertia_energy_mws(c))
# @AI_GENERATED: end