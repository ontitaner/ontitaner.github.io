"""第 18 章：命令仲裁——覆盖、叠加、合成后统一投影、未满足量与原因、审计记录。

约定：有功 kW，放电为正、充电为负。服务优先级数字**越小越重要**（P1 最高）。
安全许可和设备能力不是“请求”，而是硬约束（Limit.hard=True），任何服务都不能越过。
本模块不依赖 constraints.py，只做一维（有功）仲裁；P-Q 联合约束见 reactive.project_pq。
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Sequence

from .control import clamp


class Priority(IntEnum):
    """服务优先级（取自课程原稿），项目可调整，但必须写成配置而不是散落在代码里的数字。"""

    P1_GRID_EMERGENCY = 1  # 电网紧急稳控
    P2_FAST_SUPPORT = 2  # FFR 和快速电网支撑
    P3_DISPATCH = 3  # 一次调频、AGC、AVC、调度计划
    P4_STRATEGY_LIMIT = 4  # 防超容、防倒送、低 SOC 等策略约束
    P5_ECONOMIC = 5  # 防超需和经济优化
    P6_MAINTENANCE = 6  # 维护、校准、容量测试


@dataclass(frozen=True)
class Request:
    """服务请求。kind="setpoint" 为覆盖型基点（只取一个），"delta" 为叠加增量（例如一次调频）。"""

    source: str
    priority: int
    p_kw: float
    kind: str = "setpoint"
    valid: bool = True  # 上游数据质量/投退状态
    expires_at: float | None = None
    note: str = ""

    def __post_init__(self):
        if self.kind not in ("setpoint", "delta"):
            raise ValueError(f"未知请求类型：{self.kind}")
        if math.isnan(self.p_kw):
            raise ValueError(f"{self.source} 请求为 NaN")


@dataclass(frozen=True)
class Limit:
    """储能有功的一段允许区间 [lo, hi]。

    hard=True：安全许可、设备能力、接入协议强制要求，永远生效；
    hard=False：策略约束，带优先级，只约束“重要性不高于它”的请求。
    """

    name: str
    lo_kw: float
    hi_kw: float
    hard: bool = True
    priority: int | None = None

    def __post_init__(self):
        if not self.hard and self.priority is None:
            raise ValueError(f"策略约束 {self.name} 必须给出优先级")


# ---------------------------------------------------------------- 常用约束构造
def device_limit(available_charge_kw: float, available_discharge_kw: float, name: str = "BMS/PCS 能力") -> Limit:
    if available_charge_kw < 0 or available_discharge_kw < 0:
        raise ValueError("可充/可放能力必须是非负幅值")
    return Limit(name, -available_charge_kw, available_discharge_kw, hard=True)


def export_limit(p_load_kw: float, p_pv_kw: float, p_export_max_kw: float = 0.0, hard: bool = True,
                 priority: int | None = None, name: str = "防倒送") -> Limit:
    """P_PCC = P_PV + P_BESS − P_load ≤ 送电上限  →  P_BESS ≤ 送电上限 − P_PV + P_load。"""
    return Limit(name, -math.inf, p_export_max_kw - p_pv_kw + p_load_kw, hard, priority)


def import_limit(p_load_kw: float, p_pv_kw: float, p_import_max_kw: float, hard: bool = False,
                 priority: int | None = Priority.P5_ECONOMIC, name: str = "需量") -> Limit:
    """取电 −P_PCC ≤ 取电上限  →  P_BESS ≥ P_load − P_PV − 取电上限。"""
    return Limit(name, p_load_kw - p_pv_kw - p_import_max_kw, math.inf, hard, priority)


# ---------------------------------------------------------------- 结果
@dataclass
class ArbitrationResult:
    seq: int
    t: float
    base_source: str | None
    base_kw: float
    deltas: list[tuple[str, float]]
    composed_kw: float  # 合成后的总请求（投影前）
    effective_priority: int | None  # 参与合成的最重要请求的优先级
    lo_kw: float
    hi_kw: float
    final_kw: float
    unserved_kw: float  # composed − final（带方向）
    limiting: list[str]  # 实际起作用的约束
    rejected: list[tuple[str, str]]  # 被拒绝/覆盖的请求及原因
    skipped_limits: list[tuple[str, str]]  # 未生效的策略约束及原因
    conflict: bool = False
    notes: list[str] = field(default_factory=list)

    def as_audit(self) -> dict:
        """一条可审计记录：谁要的、谁被覆盖、合成多少、被谁限、差多少。"""
        return {
            "seq": self.seq,
            "t": self.t,
            "base": (self.base_source, self.base_kw),
            "deltas": list(self.deltas),
            "composed_kw": self.composed_kw,
            "priority": self.effective_priority,
            "bounds_kw": (self.lo_kw, self.hi_kw),
            "final_kw": self.final_kw,
            "unserved_kw": self.unserved_kw,
            "limiting": list(self.limiting),
            "rejected": list(self.rejected),
            "skipped_limits": list(self.skipped_limits),
            "conflict": self.conflict,
            "notes": list(self.notes),
        }


# ---------------------------------------------------------------- 仲裁
def arbitrate(
    requests: Sequence[Request],
    limits: Sequence[Limit],
    now: float = 0.0,
    seq: int = 0,
    default_kw: float = 0.0,
) -> ArbitrationResult:
    """① 过滤无效/过期 → ② 基点覆盖 → ③ 叠加增量 → ④ 选出生效约束 → ⑤ 统一投影一次 → ⑥ 报告未满足量。"""
    rejected: list[tuple[str, str]] = []
    notes: list[str] = []
    live: list[Request] = []
    for r in requests:
        if not r.valid:
            rejected.append((r.source, "请求无效（数据质量/未投入）"))
        elif r.expires_at is not None and now > r.expires_at:
            rejected.append((r.source, "请求已过期"))
        else:
            live.append(r)

    # ② 覆盖：基点只取最重要的一个；同级按来源名排序，保证结果确定、可复现
    setpoints = sorted((r for r in live if r.kind == "setpoint"), key=lambda r: (r.priority, r.source))
    base = setpoints[0] if setpoints else None
    for r in setpoints[1:]:
        rejected.append((r.source, f"被 {base.source}（P{base.priority}）覆盖"))
    base_kw = base.p_kw if base else default_kw
    if base is None:
        notes.append(f"无基点请求，使用默认值 {default_kw:.0f} kW")

    # ③ 叠加：增量只能叠加在“不比它更重要”的基点上；更重要的覆盖指令会连同它一起覆盖
    deltas: list[tuple[str, float]] = []
    prios = [base.priority] if base else []
    for r in (r for r in live if r.kind == "delta"):
        if base is not None and r.priority > base.priority:
            rejected.append((r.source, f"增量被 {base.source}（P{base.priority}）覆盖"))
            continue
        deltas.append((r.source, r.p_kw))
        prios.append(r.priority)
    composed = base_kw + sum(p for _, p in deltas)
    eff = min(prios) if prios else None

    # ④ 生效约束：硬约束全部生效；策略约束只约束重要性不高于它的请求
    lo, hi = -math.inf, math.inf
    hard = [c for c in limits if c.hard]
    for c in hard:
        lo, hi = max(lo, c.lo_kw), min(hi, c.hi_kw)
    conflict = False
    if lo > hi:
        conflict = True
        notes.append("硬约束互相矛盾：输出 0 并告警")
        return ArbitrationResult(seq, now, base.source if base else None, base_kw, deltas, composed, eff,
                                 lo, hi, 0.0, composed, [c.name for c in hard], rejected, [], True, notes)
    active: list[Limit] = list(hard)
    skipped: list[tuple[str, str]] = []
    for c in sorted((c for c in limits if not c.hard), key=lambda c: c.priority):
        if eff is not None and eff < c.priority:
            skipped.append((c.name, f"P{eff} 请求优先于该约束（P{c.priority}）"))
            continue
        new_lo, new_hi = max(lo, c.lo_kw), min(hi, c.hi_kw)
        if new_lo > new_hi:
            conflict = True
            skipped.append((c.name, "与更高优先级/硬约束冲突，无法满足"))
            continue
        lo, hi = new_lo, new_hi
        active.append(c)

    # ⑤ 统一投影：只做一次
    final = clamp(composed, lo, hi)
    limiting: list[str] = []
    if composed > hi:
        limiting = [c.name for c in active if c.hi_kw == hi]
    elif composed < lo:
        limiting = [c.name for c in active if c.lo_kw == lo]
    return ArbitrationResult(seq, now, base.source if base else None, base_kw, deltas, composed, eff, lo, hi,
                             final, composed - final, limiting, rejected, skipped, conflict, notes)


def naive_limit_each_then_sum(requests: Sequence[Request], limits: Sequence[Limit]) -> float:
    """反例：每个请求各自按硬约束限幅，再相加。用于演示“各自限幅相加”为什么错。"""
    lo = max((c.lo_kw for c in limits if c.hard), default=-math.inf)
    hi = min((c.hi_kw for c in limits if c.hard), default=math.inf)
    return sum(clamp(r.p_kw, lo, hi) for r in requests)

