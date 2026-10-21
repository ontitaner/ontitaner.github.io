"""第 09 章：EMS 软件控制流水线的最小可运行骨架。

一个控制周期：
① 采集（由接入层完成，传入 Measurement 字典）→ ② 校验 → ③ 状态估计 → ④ 策略
→ ⑤ 仲裁合成 → ⑥ 统一约束投影 → ⑦ Ramp + 兜底 → ⑧ 下发确认 → ⑨ 反馈记录

设计要点：
- 每一步只读上一步的输出对象，不回头读原始寄存器或全局变量；
- 先合成、后统一投影：不允许各服务分别限幅后相加；
- 每个周期产出一条 DecisionRecord，能回答“谁要的、被谁限了、发了什么、执行了多少”。

约定：功率 kW，放电为正；P_PCC 送电为正；时间 s。所有参数均为 [教学示例]。
"""
from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Callable, Mapping, Protocol, Sequence

from .control import RateLimiter, clamp, clamp_power
from .datapoint import Measurement, Quality, check_freshness, is_usable
from .frequency import PrimaryFrequencyConfig, primary_frequency_power

# 标准化后的测点名（接入层负责把厂家点表映射到这些名字，并完成方向换算）
BMS_CHG = "bms.available_charge_kw"
BMS_DIS = "bms.available_discharge_kw"
BMS_SOC = "bms.soc"
PCS_P = "pcs.p_kw"
METER_P = "meter.p_pcc_kw"
METER_F = "meter.f_hz"
AGC_TARGET = "dispatch.agc_target_kw"

# 各测点允许的最大数据年龄 [教学示例]，现场按功能的延迟预算配置
DEFAULT_MAX_AGE_S: dict[str, float] = {
    BMS_CHG: 5.0,
    BMS_DIS: 5.0,
    BMS_SOC: 10.0,
    PCS_P: 2.0,
    METER_P: 1.0,
    METER_F: 1.0,
    AGC_TARGET: 30.0,
}


# ================================================================ 数据对象分层
@dataclass(frozen=True)
class Snapshot:
    """一个周期内所有步骤共用的只读数据快照，保证“同一周期看到同一份数据”。"""

    t: float
    points: Mapping[str, Measurement]


def take_snapshot(measurements: Mapping[str, Measurement], t: float) -> Snapshot:
    return Snapshot(t, MappingProxyType(dict(measurements)))  # 复制后冻结，外部再改也不影响本周期


@dataclass(frozen=True)
class ValidatedData:
    values: Mapping[str, float]  # 通过校验、可用于控制的工程值
    rejected: Mapping[str, str]  # 未通过校验的测点及原因


@dataclass(frozen=True)
class Capability:
    """当前能力边界：可充、可放均为非负幅值。"""

    available_charge_kw: float
    available_discharge_kw: float
    source: str


@dataclass(frozen=True)
class OperatingState:
    t: float
    capability: Capability
    p_bess_kw: float | None
    p_pcc_kw: float | None
    f_hz: float | None
    soc: float | None
    agc_target_kw: float | None
    issues: tuple[str, ...] = ()

    @property
    def p_site_other_kw(self) -> float | None:
        """并网点功率中除储能以外的部分（光伏 − 负荷 − 辅助 − 损耗），用于把 PCC 限值换算成储能限值。"""
        if self.p_pcc_kw is None or self.p_bess_kw is None:
            return None
        return self.p_pcc_kw - self.p_bess_kw


@dataclass(frozen=True)
class ControlRequest:
    """策略给出的请求。kind="base" 为基点（取优先级最高的一个），"delta" 为叠加量（例如一次调频）。"""

    source: str
    p_kw: float
    kind: str
    priority: int
    reason: str


@dataclass(frozen=True)
class ConstraintResult:
    p_in_kw: float
    p_out_kw: float
    lower_kw: float
    upper_kw: float
    active: tuple[str, ...]  # 实际起作用的约束名
    conflict: bool = False  # 合规约束与设备能力冲突（可行域为空）


@dataclass(frozen=True)
class PowerCommand:
    seq: int  # 单调递增的命令序号，设备据此去重（幂等）
    cycle_id: int
    target_kw: float
    created_at: float
    expires_at: float  # 过期时间：过了这个时间，设备不应再执行
    reason: str


@dataclass(frozen=True)
class ExecutionFeedback:
    seq: int
    accepted: bool
    p_actual_kw: float | None
    ack_time: float | None
    note: str = ""


@dataclass
class DecisionRecord:
    """一个控制周期的决策记录（可追溯）。"""

    cycle_id: int
    t: float
    inputs: dict[str, tuple[float | None, str]]
    requests: list[ControlRequest]
    combined_kw: float | None = None
    constraint: ConstraintResult | None = None
    ramped_kw: float | None = None
    command: PowerCommand | None = None
    feedback: ExecutionFeedback | None = None
    issues: list[str] = field(default_factory=list)
    elapsed_s: float = 0.0
    overrun: bool = False

    def as_log(self) -> dict:
        """扁平化成一条日志：回答“谁要的、被谁限了、发了什么、执行了多少”。"""
        c, cmd, fb = self.constraint, self.command, self.feedback
        return {
            "cycle_id": self.cycle_id,
            "t": self.t,
            "requests": [(r.source, r.kind, r.p_kw) for r in self.requests],
            "request_reasons": [(r.source, r.reason) for r in self.requests],
            "combined_kw": self.combined_kw,
            "constrained_kw": c.p_out_kw if c else None,
            "bounds_kw": (c.lower_kw, c.upper_kw) if c else None,
            "active_constraints": list(c.active) if c else [],
            "constraint_conflict": c.conflict if c else None,
            "ramped_kw": self.ramped_kw,
            "final_kw": cmd.target_kw if cmd else None,
            "seq": cmd.seq if cmd else None,
            "command_reason": cmd.reason if cmd else None,
            "accepted": fb.accepted if fb else None,
            "p_actual_kw": fb.p_actual_kw if fb else None,
            "feedback_note": fb.note if fb else None,
            "issues": list(self.issues),
            "elapsed_s": self.elapsed_s,
            "overrun": self.overrun,
        }


# ================================================================ ② 校验
def validate(snapshot: Snapshot, max_age_s: Mapping[str, float]) -> ValidatedData:
    """逐点检查：存在、质量位 GOOD、按快照时刻重新判断新鲜度。"""
    values: dict[str, float] = {}
    rejected: dict[str, str] = {}
    for name, max_age in max_age_s.items():
        m = snapshot.points.get(name)
        if m is None:
            rejected[name] = "缺失"
        elif not is_usable(m):
            rejected[name] = m.quality.value
        elif (q := check_freshness(m, snapshot.t, max_age)) is not Quality.GOOD:
            rejected[name] = q.value
        else:
            values[name] = m.value
    return ValidatedData(MappingProxyType(values), MappingProxyType(rejected))


# ================================================================ ③ 状态估计
def estimate_state(data: ValidatedData, t: float, p_rated_kw: float) -> OperatingState:
    """形成统一运行状态。BMS 能力不可用时，能力取安全默认值 0（禁止充放电）。"""
    v, issues = data.values, [f"{k} 不可用：{why}" for k, why in data.rejected.items()]
    if BMS_CHG in v and BMS_DIS in v:
        cap = Capability(
            min(max(v[BMS_CHG], 0.0), p_rated_kw),  # BMS 能力与 PCS 额定取小
            min(max(v[BMS_DIS], 0.0), p_rated_kw),
            "BMS 与 PCS 额定取小",
        )
    else:
        cap = Capability(0.0, 0.0, "安全默认值：BMS 能力不可用")
    return OperatingState(
        t=t,
        capability=cap,
        p_bess_kw=v.get(PCS_P),
        p_pcc_kw=v.get(METER_P),
        f_hz=v.get(METER_F),
        soc=v.get(BMS_SOC),
        agc_target_kw=v.get(AGC_TARGET),
        issues=tuple(issues),
    )


# ================================================================ ④ 策略
class Strategy(Protocol):
    name: str

    def request(self, state: OperatingState) -> ControlRequest | None: ...


@dataclass(frozen=True)
class SlowSetpoint:
    """慢环的输出：整体替换而不是逐字段修改，快环读到的一定是一份完整、一致的结果。"""

    p_kw: float
    computed_at: float
    valid_until: float


class ScheduleStrategy:
    """计划曲线跟踪（基点）。计划值由慢环（分钟级）发布，快环每周期读取。"""

    name = "schedule"

    def __init__(self, priority: int = 10):
        self.priority = priority
        self.setpoint: SlowSetpoint | None = None

    def publish(self, p_kw: float, now: float, ttl_s: float) -> None:
        self.setpoint = SlowSetpoint(p_kw, now, now + ttl_s)  # 原子替换引用

    def request(self, state: OperatingState) -> ControlRequest | None:
        sp = self.setpoint
        if sp is None or state.t > sp.valid_until:
            return None  # 计划过期：不提请求，而不是沿用旧值
        return ControlRequest(self.name, sp.p_kw, "base", self.priority, f"计划值（{sp.computed_at:.0f} s 计算）")


class AgcStrategy:
    """AGC 跟踪（基点），优先级高于计划。调度目标不可用时不提请求，由计划或 0 兜底。"""

    name = "agc"

    def __init__(self, priority: int = 20):
        self.priority = priority

    def request(self, state: OperatingState) -> ControlRequest | None:
        if state.agc_target_kw is None:
            return None
        return ControlRequest(self.name, state.agc_target_kw, "base", self.priority, "调度 AGC 目标")


class PrimaryFrequencyStrategy:
    """一次调频（叠加量）。频率数据不可用时退出，不输出。"""

    name = "pfr"

    def __init__(self, cfg: PrimaryFrequencyConfig, priority: int = 30):
        self.cfg = cfg
        self.priority = priority

    def request(self, state: OperatingState) -> ControlRequest | None:
        if state.f_hz is None:
            return None
        dp = primary_frequency_power(state.f_hz, self.cfg)
        return ControlRequest(self.name, dp, "delta", self.priority, f"f={state.f_hz:.3f} Hz 下垂")


# ================================================================ ⑤ 仲裁合成
def arbitrate(requests: Sequence[ControlRequest]) -> tuple[float, list[ControlRequest]]:
    """最小仲裁规则：基点取优先级最高的一个 + 所有叠加量之和。完整规则见第 18 章。"""
    bases = [r for r in requests if r.kind == "base"]
    deltas = [r for r in requests if r.kind == "delta"]
    used = ([max(bases, key=lambda r: r.priority)] if bases else []) + deltas
    return sum(r.p_kw for r in used), used


def naive_limit_each_then_sum(requests: Sequence[ControlRequest], cap: Capability) -> float:
    """反例：每个服务各自按能力限幅，再相加。仅用于演示为什么不能这样做。"""
    return sum(clamp_power(r.p_kw, cap.available_charge_kw, cap.available_discharge_kw) for r in requests)


# ================================================================ ⑥ 统一约束投影
def project(
    p_kw: float,
    state: OperatingState,
    pcc_export_limit_kw: float | None = None,
    pcc_import_limit_kw: float | None = None,
) -> ConstraintResult:
    """把合成后的总请求压进可行域。

    设备能力是硬约束；并网点限值（防倒送、需量）换算成储能功率的上下限后求交集。
    交集为空（冲突）时：保持在设备能力内、尽量靠近合规区间，并标记 conflict 上报。
    """
    cap = state.capability
    lo, hi = -cap.available_charge_kw, cap.available_discharge_kw
    lo_name, hi_name = "可充能力", "可放能力"

    c_lo, c_hi, c_lo_name, c_hi_name = -math.inf, math.inf, "", ""
    other = state.p_site_other_kw
    if pcc_export_limit_kw is not None:  # P_PCC = other + P_BESS ≤ 送电上限
        if other is None:
            c_hi, c_hi_name = 0.0, "防倒送（电表不可用，保守禁放）"
        else:
            c_hi, c_hi_name = pcc_export_limit_kw - other, "防倒送"
    if pcc_import_limit_kw is not None:  # −P_PCC ≤ 取电上限
        if other is None:
            c_lo, c_lo_name = 0.0, "需量（电表不可用，保守禁充）"
        else:
            c_lo, c_lo_name = -pcc_import_limit_kw - other, "需量"

    conflict = False
    new_lo, new_hi = max(lo, c_lo), min(hi, c_hi)
    if new_lo <= new_hi:
        if c_lo > lo:
            lo, lo_name = c_lo, c_lo_name
        if c_hi < hi:
            hi, hi_name = c_hi, c_hi_name
    else:
        conflict = True  # 合规要求超出设备能力：取设备能力内离合规区间最近的点
        need_more_discharge = c_lo > hi
        point = hi if need_more_discharge else lo
        name = f"冲突：{c_lo_name if need_more_discharge else c_hi_name}超出设备能力"
        lo, hi, lo_name, hi_name = point, point, name, name

    out = clamp(p_kw, lo, hi)
    active = tuple(n for n, hit in ((hi_name, p_kw > hi), (lo_name, p_kw < lo)) if hit)
    if conflict and not active:
        active = (lo_name,)
    return ConstraintResult(p_kw, out, lo, hi, active, conflict)


# ================================================================ ⑧ 设备（教学替身）
class MockPcs:
    """PCS 替身：按序号去重（幂等），拒绝过期指令，按 tracking 比例执行。"""

    def __init__(self, p_rated_kw: float, tracking: float = 1.0, ack_delay_s: float = 0.05):
        self.p_rated_kw = p_rated_kw
        self.tracking = tracking
        self.ack_delay_s = ack_delay_s
        self.last_seq = 0
        self.p_actual_kw = 0.0
        self.executed: list[int] = []  # 真正执行过的序号，用于验证“不重复执行”

    def apply(self, cmd: PowerCommand, now: float) -> ExecutionFeedback:
        ack = now + self.ack_delay_s
        if cmd.seq == self.last_seq:
            return ExecutionFeedback(cmd.seq, True, self.p_actual_kw, ack, "重复序号：已执行过，不再执行")
        if cmd.seq < self.last_seq:
            return ExecutionFeedback(cmd.seq, False, self.p_actual_kw, ack, "旧序号：拒绝")
        if now > cmd.expires_at:
            return ExecutionFeedback(cmd.seq, False, self.p_actual_kw, ack, "指令已过期：拒绝")
        if abs(cmd.target_kw) > self.p_rated_kw:
            return ExecutionFeedback(cmd.seq, False, self.p_actual_kw, ack, "超出额定：拒绝")
        self.last_seq = cmd.seq
        self.p_actual_kw = cmd.target_kw * self.tracking
        self.executed.append(cmd.seq)
        return ExecutionFeedback(cmd.seq, True, self.p_actual_kw, ack)


class CommandSink(Protocol):
    def apply(self, cmd: PowerCommand, now: float) -> ExecutionFeedback: ...


# ================================================================ 流水线
@dataclass
class PipelineConfig:
    p_rated_kw: float
    dt_s: float = 0.2  # 快环周期 [教学示例]
    cycle_budget_s: float = 0.1  # 本周期计算必须在此时间内完成 [教学示例]
    ramp_kw_per_s: float = 1000.0  # [教学示例]
    command_ttl_s: float = 2.0  # 指令有效期 [教学示例]
    pcc_export_limit_kw: float | None = None
    pcc_import_limit_kw: float | None = None
    max_age_s: dict[str, float] = field(default_factory=lambda: dict(DEFAULT_MAX_AGE_S))


class ControlPipeline:
    def __init__(
        self,
        cfg: PipelineConfig,
        strategies: Sequence[Strategy],
        sink: CommandSink,
        clock: Callable[[], float] = time.monotonic,
        seq_start: int = 0,
        p_initial_kw: float = 0.0,
    ):
        self.cfg = cfg
        self.strategies = list(strategies)
        self.sink = sink
        self.clock = clock  # 用于测量本周期耗时；测试中可注入假时钟
        self.seq = seq_start
        self.cycle_id = 0
        self.ramp = RateLimiter(cfg.ramp_kw_per_s, cfg.ramp_kw_per_s, initial=p_initial_kw)
        self.last_sent_kw = p_initial_kw
        self.missed_deadlines = 0

    # ------------------------------------------------------------ 重启恢复
    def recover(self, p_actual_kw: float, last_seq: int) -> None:
        """重启后：Ramp 从实测功率起步，序号从持久化的最后序号继续；不重放旧命令。"""
        self.ramp.reset(p_actual_kw)
        self.last_sent_kw = p_actual_kw
        self.seq = last_seq

    # ------------------------------------------------------------ 一个控制周期
    def run_cycle(self, measurements: Mapping[str, Measurement], now: float) -> DecisionRecord:
        self.cycle_id += 1
        start = self.clock()
        snap = take_snapshot(measurements, now)  # ① 采集结果冻结成快照
        rec = DecisionRecord(
            self.cycle_id, now, {k: (m.value, m.quality.value) for k, m in snap.points.items()}, []
        )
        try:
            data = validate(snap, self.cfg.max_age_s)  # ②
            state = estimate_state(data, now, self.cfg.p_rated_kw)  # ③
            rec.issues.extend(state.issues)
            for s in self.strategies:  # ④ 异常隔离：一个策略出错不影响其他策略
                try:
                    r = s.request(state)
                except Exception as exc:  # noqa: BLE001 教学示例：记录后跳过
                    rec.issues.append(f"策略 {s.name} 异常：{exc!r}，本周期忽略")
                    continue
                if r is not None:
                    rec.requests.append(r)
            combined, _ = arbitrate(rec.requests)  # ⑤
            rec.combined_kw = combined
            res = project(combined, state, self.cfg.pcc_export_limit_kw, self.cfg.pcc_import_limit_kw)  # ⑥
            rec.constraint = res
            if res.conflict:
                rec.issues.append(f"约束冲突：{res.active}")
            ramped = self.ramp.update(res.p_out_kw, self.cfg.dt_s)  # ⑦ Ramp
            final = clamp(ramped, res.lower_kw, res.upper_kw)  # 兜底：能力收缩立即生效
            if final != ramped:
                self.ramp.reset(final)
            rec.ramped_kw = final
        except Exception as exc:  # noqa: BLE001 未预期异常：本周期不下发，PCS 保持上一指令
            rec.issues.append(f"周期异常：{exc!r}，本周期不下发")
            self.ramp.reset(self.last_sent_kw)
            rec.elapsed_s = self.clock() - start
            return rec

        rec.elapsed_s = self.clock() - start
        if rec.elapsed_s > self.cfg.cycle_budget_s:  # 超时：数据已不新鲜，放弃本周期
            rec.overrun = True
            self.missed_deadlines += 1
            rec.issues.append(f"周期超时 {rec.elapsed_s:.3f} s，本周期不下发，PCS 保持上一指令")
            self.ramp.reset(self.last_sent_kw)
            return rec

        self.seq += 1  # ⑧ 下发与确认
        cmd = PowerCommand(self.seq, self.cycle_id, final, now, now + self.cfg.command_ttl_s,
                           "+".join(r.source for r in rec.requests) or "无请求")
        rec.command = cmd
        rec.feedback = self.sink.apply(cmd, now)
        if rec.feedback.accepted:
            self.last_sent_kw = final
        else:
            rec.issues.append(f"指令 #{cmd.seq} 被拒绝：{rec.feedback.note}")
            self.ramp.reset(self.last_sent_kw)
        return rec  # ⑨ 记录由调用方写入日志/历史库

