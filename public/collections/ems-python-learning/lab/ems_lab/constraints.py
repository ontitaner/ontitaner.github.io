"""第 12 章：安全约束与可行域。

核心思想：
1. 每个约束都给出储能功率 P_BESS 的一个允许区间 [下限, 上限]；
2. 最终可行域 = 所有区间的交集；
3. 把策略请求投影进可行域（一维就是 clamp）；
4. 交集为空（约束冲突）时，按优先级从低到高放松，并且必须记录、上报，绝不静默。

约定：功率单位 kW；P_BESS 放电为正、充电为负；P_PCC 向电网送电为正；
P_import = −P_PCC（从电网取电为正），只用于进口上限（防超容/需量）。
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Sequence

from .control import Hysteresis, PIController, clamp, interp_table

INF = math.inf


class Layer(IntEnum):
    """约束来源分层，数字越小越优先。"""

    HARD_SAFETY = 0  # ① 硬安全许可：BMS/PCS 保护、继保、消防、检修闭锁。只能服从
    DEVICE = 1  # ② 设备能力：BMS/PCS 可充/可放、温度、SOC 分区
    SITE = 2  # ③ 站点约束：防超容、防倒送、进口上限、防非计划充电
    STRATEGY = 3  # ④ 策略目标：例如某个策略要求的功率窗口

    @property
    def relaxable(self) -> bool:
        """①② 是物理事实，放松它们等于让设备越限；只有 ③④ 在冲突时可以被放松（并上报）。"""
        return self >= Layer.SITE


@dataclass(frozen=True)
class Interval:
    """一个约束给出的 P_BESS 允许区间 [lower_kw, upper_kw]。

    name 和 note 用于日志：事后必须能回答“是谁、按什么数算出来的这个边界”。
    priority 用于同一层内排序（越小越优先）。
    """

    lower_kw: float
    upper_kw: float
    name: str
    layer: Layer
    note: str = ""
    priority: int = 0

    def __post_init__(self):
        if math.isnan(self.lower_kw) or math.isnan(self.upper_kw):
            raise ValueError(f"约束 {self.name} 的边界含 NaN，应在数据校验层拦截")

    @property
    def is_empty(self) -> bool:
        return self.lower_kw > self.upper_kw

    def contains(self, p_kw: float) -> bool:
        return self.lower_kw <= p_kw <= self.upper_kw


def intersect(intervals: Sequence[Interval]) -> tuple[float, float]:
    """纯交集：返回 (下限, 上限)。结果可能为空（下限 > 上限），由调用方处理。"""
    lo = max((c.lower_kw for c in intervals), default=-INF)
    hi = min((c.upper_kw for c in intervals), default=INF)
    return lo, hi


# ---------------------------------------------------------------- ① 硬安全许可
def permission_interval(allow_charge: bool, allow_discharge: bool, name: str = "安全许可") -> Interval:
    """把外部安全系统的“允许充电/允许放电”许可翻译成区间。

    它不是一个请求，而是一个事实：禁止放电时上限就是 0，任何策略都不能改变。
    """
    return Interval(
        lower_kw=-INF if allow_charge else 0.0,
        upper_kw=INF if allow_discharge else 0.0,
        name=name,
        layer=Layer.HARD_SAFETY,
        note=f"允许充电={allow_charge}，允许放电={allow_discharge}",
    )


# ---------------------------------------------------------------- ② 设备能力
def device_interval(available_charge_kw: float, available_discharge_kw: float, name: str = "BMS/PCS 能力") -> Interval:
    """设备可充/可放能力（非负幅值）→ 区间 [−可充, +可放]。与第 11 章 clamp_power 一致。"""
    if available_charge_kw < 0 or available_discharge_kw < 0:
        raise ValueError("可充/可放能力必须是非负幅值，接入层要统一换算")
    return Interval(-available_charge_kw, available_discharge_kw, name, Layer.DEVICE,
                    note=f"可充 {available_charge_kw:g}，可放 {available_discharge_kw:g}")


@dataclass(frozen=True)
class SocZoneConfig:
    """SOC 运行窗口参数（0~1），与第 05 章 SocZones 的运行下限/预警下限/预警上限/运行上限一致。

    全部为 [教学示例]，现场以电池厂家和项目策略为准。
    EMS 的运行窗口应当比 BMS 的保护窗口更窄：EMS 先“软停”，BMS 的硬保护不应该被频繁触发。
    """

    stop_discharge_at: float = 0.10  # 运行下限：SOC ≤ 10% 禁止放电
    full_discharge_from: float = 0.15  # 预警下限：10%～15% 放电线性降额
    full_charge_until: float = 0.85  # 预警上限：85%～90% 充电线性降额
    stop_charge_at: float = 0.90  # 运行上限：SOC ≥ 90% 禁止充电

    def __post_init__(self):
        if not (0 <= self.stop_discharge_at < self.full_discharge_from
                < self.full_charge_until < self.stop_charge_at <= 1):
            raise ValueError("SOC 分区阈值必须严格递增")


def soc_interval(soc: float, p_rated_kw: float, cfg: SocZoneConfig = SocZoneConfig()) -> Interval:
    """SOC 分区保护：SOC 越低，放电上限越小；SOC 越高，充电上限越小（分区之间线性过渡）。

    线性过渡而不是台阶：台阶会让功率在阈值附近跳变，配合测量噪声就会来回抖。
    """
    if not 0 <= soc <= 1:
        raise ValueError(f"SOC={soc} 超出 0～1，检查单位（代码里 SOC 用 0～1）")
    dis = interp_table(soc, [cfg.stop_discharge_at, cfg.full_discharge_from], [0.0, 1.0])
    chg = interp_table(soc, [cfg.full_charge_until, cfg.stop_charge_at], [1.0, 0.0])
    return Interval(-p_rated_kw * chg, p_rated_kw * dis, "SOC 分区", Layer.DEVICE,
                    note=f"SOC={soc:.1%}：放电比例 {dis:.0%}，充电比例 {chg:.0%}")


class LowSocRecharge:
    """低 SOC 自充：SOC 低于 start_below 时发出充电请求，高于 stop_above 才停止（第 11 章滞回）。

    注意它输出的是“请求”，不是约束：自充请求同样要经过可行域投影，
    例如进口上限（需量、防超容）仍然可以把它削小。参数为 [教学示例]。
    """

    def __init__(self, start_below: float = 0.08, stop_above: float = 0.15, p_charge_kw: float = 200.0,
                 initial: bool = False):
        if p_charge_kw <= 0:
            raise ValueError("自充功率用正的幅值配置")
        self._hyst = Hysteresis(on_below=start_below, off_above=stop_above, initial=initial)
        self.p_charge_kw = p_charge_kw

    @property
    def active(self) -> bool:
        return self._hyst.active

    def update(self, soc: float) -> float | None:
        """返回自充请求功率（负数 = 充电）；不需要自充时返回 None。"""
        return -self.p_charge_kw if self._hyst.update(soc) else None


# ---------------------------------------------------------------- ③ 站点约束
def export_limit_interval(p_load_kw: float, p_pv_kw: float, p_export_limit_kw: float = 0.0,
                          p_aux_kw: float = 0.0, p_loss_kw: float = 0.0,
                          name: str = "防倒送") -> Interval:
    """防倒送/出口上限推出的储能放电上限。

    P_PCC = P_PV + P_BESS − P_load − P_aux − P_loss ≤ P_export_limit
    ⇒ P_BESS ≤ P_load + P_aux + P_loss − P_PV + P_export_limit

    结果可能是负数：光伏富余时，储能必须“至少充这么多”才能不倒送。
    """
    if p_export_limit_kw < 0:
        raise ValueError("出口上限用非负数表示；零倒送就是 0")
    upper = p_load_kw + p_aux_kw + p_loss_kw - p_pv_kw + p_export_limit_kw
    note = (f"上限 = 负荷 {p_load_kw:g} + 辅助 {p_aux_kw:g} + 损耗 {p_loss_kw:g} − 光伏 {p_pv_kw:g} "
            f"+ 出口上限 {p_export_limit_kw:g} = {upper:g}")
    return Interval(-INF, upper, name, Layer.SITE, note=note)


def import_limit_interval(p_load_kw: float, p_pv_kw: float, p_import_limit_kw: float,
                          p_aux_kw: float = 0.0, p_loss_kw: float = 0.0,
                          name: str = "进口上限", priority: int = 0) -> Interval:
    """进口上限（防超容 / 需量目标）推出的储能充电上限（区间下限）。

    P_import = −P_PCC = P_load + P_aux + P_loss − P_PV − P_BESS ≤ P_import_limit
    ⇒ P_BESS ≥ P_load + P_aux + P_loss − P_PV − P_import_limit

    结果为负：最多还能充这么多；结果为正：储能必须“至少放这么多”才能不超限。
    """
    lower = p_load_kw + p_aux_kw + p_loss_kw - p_pv_kw - p_import_limit_kw
    note = (f"下限 = 负荷 {p_load_kw:g} + 辅助 {p_aux_kw:g} + 损耗 {p_loss_kw:g} − 光伏 {p_pv_kw:g} "
            f"− 进口上限 {p_import_limit_kw:g} = {lower:g}")
    return Interval(lower, INF, name, Layer.SITE, note=note, priority=priority)


def no_grid_charge_interval(p_load_kw: float, p_pv_kw: float, p_aux_kw: float = 0.0,
                            p_loss_kw: float = 0.0, name: str = "防非计划充电") -> Interval:
    """防非计划充电：不允许从电网取电给储能充电，只允许吸收光伏富余。

    它只限制充电，不会强迫储能放电——这是它和“进口上限 = 0”的区别。
    """
    surplus = p_pv_kw - p_load_kw - p_aux_kw - p_loss_kw
    lower = -max(0.0, surplus)
    return Interval(lower, INF, name, Layer.SITE, note=f"光伏富余 {surplus:g}，充电下限 {lower:g}")


class BoundCorrector:
    """并网点实测闭环修正：前馈（开环）算出的边界 + PI 修正量（第 11 章 PIController）。

    为什么需要：前馈公式依赖负荷、光伏等测量值，而现场总有测不到或测不准的部分
    （未计量的小光伏、CT 误差、未建模的损耗）。并网点电表测的是“结果”，用它闭环修正。

    margin_kw = 离限值还有多少余量（> 0 安全，< 0 已越限）。
    返回修正量：> 0 放宽边界，< 0 收紧边界。
      - 上限类（防倒送）：upper = 前馈上限 + 修正量；
      - 下限类（进口上限）：lower = 前馈下限 − 修正量。
    抗饱和：约束不起作用（active=False）且还有余量时不积分“余量”，
    否则积分会越攒越大，约束真正起作用的那一刻第一拍就越限；越限时总是积分（收紧）。
    """

    def __init__(self, kp: float, ki: float, max_correction_kw: float):
        if max_correction_kw < 0:
            raise ValueError("修正量上限必须非负")
        self.pi = PIController(kp, ki, -max_correction_kw, max_correction_kw)

    def update(self, margin_kw: float, dt: float, active: bool) -> float:
        e = margin_kw if (active or margin_kw < 0) else 0.0
        return self.pi.update(e, dt)

    def reset(self) -> None:
        self.pi.reset()


# ---------------------------------------------------------------- 投影与冲突处理
@dataclass(frozen=True)
class Conflict:
    """一次约束冲突：约束 name 要求 [lower_kw, upper_kw]，但更高优先级的可行域够不到。"""

    name: str
    layer: Layer
    lower_kw: float
    upper_kw: float
    shortfall_kw: float  # 离满足该约束还差多少 kW


@dataclass
class ConstraintResult:
    """约束投影结果：不仅给出最终功率，还要说明为什么是这个数。"""

    requested_kw: float
    final_kw: float
    lower_kw: float
    upper_kw: float
    binding: str | None = None  # 把请求截断的那个约束
    conflicts: list[Conflict] = field(default_factory=list)
    safe_stop: bool = False  # 不可放松的约束之间冲突：输出 0 并告警

    @property
    def limited(self) -> bool:
        return self.final_kw != self.requested_kw

    def reasons(self) -> list[str]:
        out: list[str] = []
        if self.safe_stop:
            out.append("不可放松的约束之间冲突，输出 0 kW 并告警")
        for c in self.conflicts:
            out.append(f"约束冲突：【{c.name}】无法满足，缺口 {c.shortfall_kw:.0f} kW，已放松并上报")
        if self.binding and self.limited:
            out.append(f"请求 {self.requested_kw:+.0f} kW 被【{self.binding}】限制为 {self.final_kw:+.0f} kW")
        return out


def project(request_kw: float, constraints: Sequence[Interval]) -> ConstraintResult:
    """把请求投影进可行域，并在冲突时按优先级放松。

    算法（按 layer、priority 从高到低逐个加入约束）：
    - 与当前可行域有交集：收缩可行域；
    - 没有交集且该约束可放松（③④）：记录冲突和缺口，可行域收缩为“最接近该约束的那个边界点”，
      即在不违反更高优先级约束的前提下尽力而为；
    - 没有交集且不可放松（①②之间冲突）：说明输入数据本身矛盾，输出 0 kW 并标记 safe_stop。
    最后 final = clamp(request, 下限, 上限)。
    """
    if math.isnan(request_kw):
        raise ValueError("请求功率为 NaN，应在策略层或数据校验层拦截")
    lo, hi = -INF, INF
    lo_src: str | None = None
    hi_src: str | None = None
    conflicts: list[Conflict] = []
    for c in sorted(constraints, key=lambda x: (x.layer, x.priority)):
        if c.is_empty:
            raise ValueError(f"约束 {c.name} 自身为空区间：{c.lower_kw} > {c.upper_kw}")
        new_lo, new_hi = max(lo, c.lower_kw), min(hi, c.upper_kw)
        if new_lo <= new_hi:
            if c.lower_kw > lo:
                lo, lo_src = c.lower_kw, c.name
            if c.upper_kw < hi:
                hi, hi_src = c.upper_kw, c.name
            continue
        # 交集为空：c 与更高优先级的可行域冲突
        shortfall = c.lower_kw - hi if c.lower_kw > hi else lo - c.upper_kw
        conflicts.append(Conflict(c.name, c.layer, c.lower_kw, c.upper_kw, shortfall))
        if not c.layer.relaxable:
            return ConstraintResult(request_kw, 0.0, 0.0, 0.0, binding=c.name,
                                    conflicts=conflicts, safe_stop=True)
        # 尽力而为：取已有可行域中离 c 最近的边界点
        if c.lower_kw > hi:
            lo, lo_src = hi, hi_src
        else:
            hi, hi_src = lo, lo_src
    final = clamp(request_kw, lo, hi)
    binding = None
    if final < request_kw:
        binding = hi_src
    elif final > request_kw:
        binding = lo_src
    return ConstraintResult(request_kw, final, lo, hi, binding=binding, conflicts=conflicts)

