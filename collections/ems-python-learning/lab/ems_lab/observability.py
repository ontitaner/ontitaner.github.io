"""第 20 章：运维与可观测性——告警生命周期、控制决策审计、参数一致性核对、SOE 排序、运行 KPI。

约定：P 放电为正，功率 kW，电量 kWh，时间 s（SOE 用 ms 整数）。
告警分级、延时、滞回阈值均为 [教学示例]，现场以项目告警定义表和设备厂家资料为准。
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum, IntEnum

from .control import clamp


# ================================================================ 告警
class Severity(IntEnum):
    """站内统一分级（数字越小越严重）。设备自带的分级要在接入层映射到这里。"""

    CRITICAL = 1  # 一级：事故/紧急，立即处置（消防动作、急停、保护跳闸）
    MAJOR = 2  # 二级：异常，尽快处置（通信中断、降额运行、数据失效）
    MINOR = 3  # 三级：提示，关注趋势（温度偏高、SOC 偏低）


class AlarmState(str, Enum):
    NORMAL = "正常"
    ACTIVE_UNACK = "活动-未确认"
    ACTIVE_ACK = "活动-已确认"
    CLEARED_UNACK = "已恢复-未确认"
    CLOSED = "已关闭"


@dataclass(frozen=True)
class AlarmRule:
    code: str
    name: str
    severity: Severity
    raise_at: float  # 越过此值产生
    clear_at: float  # 回到此值另一侧才恢复（滞回）
    high: bool = True  # True：越上限告警；False：越下限告警
    on_delay_s: float = 0.0  # 持续这么久才产生（防抖）
    off_delay_s: float = 0.0  # 持续恢复这么久才算恢复
    latched: bool = False  # 闭锁型：条件消失后仍保持，需人工复归

    def __post_init__(self):
        if self.high and self.clear_at >= self.raise_at:
            raise ValueError("越上限告警：恢复阈值必须低于产生阈值")
        if not self.high and self.clear_at <= self.raise_at:
            raise ValueError("越下限告警：恢复阈值必须高于产生阈值")

    def beyond_raise(self, v: float) -> bool:
        return v > self.raise_at if self.high else v < self.raise_at

    def beyond_clear(self, v: float) -> bool:
        return v < self.clear_at if self.high else v > self.clear_at


@dataclass
class AlarmRecord:
    alarm_id: int
    code: str
    source: str
    severity: Severity
    state: AlarmState
    t_raised: float
    value_raised: float
    peak_value: float
    occurrences: int = 1  # 去重：未关闭期间再次越限只计数，不新建告警
    condition_present: bool = True
    t_acked: float | None = None
    acked_by: str | None = None
    t_cleared: float | None = None
    t_closed: float | None = None
    closed_by: str | None = None


@dataclass
class _Channel:
    record: AlarmRecord | None = None
    pending_since: float | None = None  # 越限开始计时
    clearing_since: float | None = None  # 恢复开始计时


class AlarmManager:
    """按 (告警码, 设备) 维护告警生命周期：产生 → 确认 → 恢复 → 关闭，带延时、滞回、去重、闭锁。"""

    def __init__(self, rules: list[AlarmRule]):
        self.rules = {r.code: r for r in rules}
        self._channels: dict[tuple[str, str], _Channel] = {}
        self._next_id = 1
        self.records: list[AlarmRecord] = []
        self.log: list[tuple[float, int, str]] = []  # (时刻, 告警号, 动作)

    def _transition(self, t: float, rec: AlarmRecord, state: AlarmState, action: str) -> None:
        rec.state = state
        self.log.append((t, rec.alarm_id, action))

    def update(self, t: float, source: str, code: str, value: float) -> AlarmRecord | None:
        rule = self.rules[code]
        ch = self._channels.setdefault((code, source), _Channel())
        rec = ch.record

        if rule.beyond_raise(value):
            ch.clearing_since = None
            ch.pending_since = t if ch.pending_since is None else ch.pending_since
            if rec is not None:
                rec.peak_value = max(rec.peak_value, value) if rule.high else min(rec.peak_value, value)
            if t - ch.pending_since >= rule.on_delay_s:
                if rec is None:
                    rec = AlarmRecord(self._next_id, code, source, rule.severity, AlarmState.ACTIVE_UNACK,
                                      t, value, value)
                    self._next_id += 1
                    self.records.append(rec)
                    ch.record = rec
                    self.log.append((t, rec.alarm_id, "产生"))
                elif not rec.condition_present:
                    rec.condition_present = True
                    rec.occurrences += 1
                    if rec.state is AlarmState.CLEARED_UNACK:
                        self._transition(t, rec, AlarmState.ACTIVE_UNACK, "再次越限")
                    else:
                        self.log.append((t, rec.alarm_id, "再次越限"))
        elif rule.beyond_clear(value):
            ch.pending_since = None
            if rec is not None and rec.condition_present:
                ch.clearing_since = t if ch.clearing_since is None else ch.clearing_since
                if t - ch.clearing_since >= rule.off_delay_s:
                    rec.condition_present = False
                    rec.t_cleared = t
                    if rule.latched:
                        self.log.append((t, rec.alarm_id, "条件消失，等待人工复归"))
                    elif rec.state is AlarmState.ACTIVE_ACK:
                        self._close(t, ch, "自动恢复并关闭", None)
                    else:
                        self._transition(t, rec, AlarmState.CLEARED_UNACK, "恢复")
        else:  # 处在滞回带内：保持原状态，计时清零
            ch.pending_since = None
            ch.clearing_since = None
        return ch.record

    def _close(self, t: float, ch: _Channel, action: str, user: str | None) -> None:
        rec = ch.record
        rec.t_closed, rec.closed_by = t, user
        self._transition(t, rec, AlarmState.CLOSED, action)
        ch.record = None

    def _channel_of(self, alarm_id: int) -> _Channel:
        for ch in self._channels.values():
            if ch.record is not None and ch.record.alarm_id == alarm_id:
                return ch
        raise KeyError(f"告警 {alarm_id} 不存在或已关闭")

    def ack(self, t: float, alarm_id: int, user: str) -> None:
        """确认 = 有人看到了，不等于问题解决。"""
        ch = self._channel_of(alarm_id)
        rec = ch.record
        if rec.t_acked is None:
            rec.t_acked, rec.acked_by = t, user
        if rec.state is AlarmState.ACTIVE_UNACK:
            self._transition(t, rec, AlarmState.ACTIVE_ACK, f"确认({user})")
        elif rec.state is AlarmState.CLEARED_UNACK:
            self._close(t, ch, f"确认并关闭({user})", user)

    def reset(self, t: float, alarm_id: int, user: str) -> None:
        """闭锁型告警的人工复归：条件必须已经消失，且已经确认。"""
        ch = self._channel_of(alarm_id)
        rec = ch.record
        if rec.condition_present:
            raise ValueError("条件仍存在，不允许复归")
        if rec.t_acked is None:
            raise ValueError("未确认的告警不允许复归")
        self._close(t, ch, f"人工复归({user})", user)

    def active(self) -> list[AlarmRecord]:
        return [ch.record for ch in self._channels.values() if ch.record is not None]


def naive_alarm_count(values: list[float], threshold: float) -> int:
    """反例：单阈值、无延时，每次从下往上穿越都算一条新告警。"""
    return sum(1 for a, b in zip(values, values[1:]) if a <= threshold < b)


# ================================================================ 控制决策审计
@dataclass(frozen=True)
class Limit:
    name: str
    lower_kw: float
    upper_kw: float


@dataclass(frozen=True)
class LimitStep:
    name: str
    lower_kw: float
    upper_kw: float
    before_kw: float
    after_kw: float

    @property
    def binding(self) -> bool:
        return self.after_kw != self.before_kw


def apply_limit_chain(requested_kw: float, limits: list[Limit]) -> tuple[float, list[LimitStep]]:
    """按流水线顺序逐个限幅，并记录每一步前后的值——“为什么只发了这么多”的答案就在这里。"""
    p = requested_kw
    steps = []
    for lim in limits:
        after = clamp(p, lim.lower_kw, lim.upper_kw)
        steps.append(LimitStep(lim.name, lim.lower_kw, lim.upper_kw, p, after))
        p = after
    return p, steps


@dataclass
class DecisionAudit:
    cycle_id: int
    seq: int
    t_mono_s: float  # 单调时间：排序、算间隔
    t_wall: str  # 墙钟：给人看、和其他系统对时
    mode: str
    requests: list[tuple[str, float]]  # (来源, kW)
    requested_kw: float
    steps: list[LimitStep]
    final_kw: float
    soc: float
    avail_charge_kw: float
    avail_discharge_kw: float
    data_quality: dict[str, str]
    config_version: str
    software_version: str
    ack: str | None = None  # 设备回应：接受/拒绝原因
    actual_kw: float | None = None  # 下一周期回填

    def binding(self) -> list[str]:
        return [s.name for s in self.steps if s.binding]

    def explain(self) -> str:
        src = "、".join(f"{n} {v:g}" for n, v in self.requests)
        parts = [f"请求 {self.requested_kw:g} kW（{src}）"]
        for s in self.steps:
            tag = f"压到 {s.after_kw:g}" if s.binding else "未限制"
            parts.append(f"{s.name} [{s.lower_kw:g}, {s.upper_kw:g}] {tag}")
        parts.append(f"下发 {self.final_kw:g} kW")
        if self.actual_kw is not None:
            parts.append(f"实际 {self.actual_kw:g} kW")
        return " → ".join(parts)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["binding"] = self.binding()
        return d


# ================================================================ 参数一致性
@dataclass(frozen=True)
class ParamMismatch:
    name: str
    expected: float
    actual: float | None
    note: str


def check_param_consistency(
    expected: dict[str, float], readback: dict[str, float | None], rel_tol: float = 0.01, abs_tol: float = 1e-6
) -> list[ParamMismatch]:
    """EMS 配置 vs 设备实际运行参数（读回值）。缺失、读失败也算不一致——“没读到”不等于“一样”。"""
    out = []
    for name, exp in expected.items():
        act = readback.get(name)
        if act is None:
            out.append(ParamMismatch(name, exp, None, "设备未上送或读取失败"))
        elif abs(act - exp) > max(abs_tol, rel_tol * abs(exp)):
            out.append(ParamMismatch(name, exp, act, "数值不一致"))
    return out


# ================================================================ SOE
@dataclass(frozen=True)
class SoeEvent:
    t_ms: int  # 设备打的时标（毫秒），不是 EMS 收到的时间
    device: str
    point: str
    value: int
    t_received_ms: int = 0


def soe_sequence(events: list[SoeEvent]) -> list[SoeEvent]:
    """按设备时标排序还原事件顺序；到达顺序受轮询和网络影响，不能用来判断先后。"""
    return sorted(events, key=lambda e: (e.t_ms, e.device, e.point))


# ================================================================ 运行 KPI
def availability(period_s: float, outages: list[tuple[float, float]]) -> float:
    """可用率 = 1 − 不可用时长 / 统计时长。重叠的停运区间先合并，避免重复扣减。"""
    if period_s <= 0:
        raise ValueError("统计时长必须为正")
    merged: list[list[float]] = []
    for a, b in sorted(outages):
        if b < a:
            raise ValueError("停运区间结束早于开始")
        a, b = max(a, 0.0), min(b, period_s)
        if merged and a <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], b)
        elif b > a:
            merged.append([a, b])
    down = sum(b - a for a, b in merged)
    return 1.0 - down / period_s


def round_trip_efficiency(
    e_charge_kwh: float, e_discharge_kwh: float, soc_start: float, soc_end: float, usable_kwh: float
) -> float:
    """往返效率 ≈ (放电量 + 期末多存下的电量) / 充电量。[教学近似]

    最好选首尾 SOC 相同的统计周期；否则按 ΔSOC × 可用容量修正。
    计量点（PCS 交流侧 / 并网点，是否含站用电）必须写明，不同计量点的结果差别很大。
    """
    if e_charge_kwh <= 0:
        raise ValueError("充电量必须为正")
    return (e_discharge_kwh + (soc_end - soc_start) * usable_kwh) / e_charge_kwh


@dataclass
class TrackingStats:
    mean_abs_kw: float
    max_abs_kw: float
    within_ratio: float  # 偏差在容差内的样本比例


def tracking_error(cmd_kw: list[float], actual_kw: list[float], tol_kw: float) -> TrackingStats:
    if len(cmd_kw) != len(actual_kw) or not cmd_kw:
        raise ValueError("指令和实际序列必须等长且非空")
    errs = [abs(c - a) for c, a in zip(cmd_kw, actual_kw)]
    return TrackingStats(sum(errs) / len(errs), max(errs), sum(e <= tol_kw for e in errs) / len(errs))


def success_rate(ok: int, total: int) -> float:
    if total <= 0:
        raise ValueError("总次数必须为正")
    return ok / total


def count_binding(audits: list[DecisionAudit], name: str) -> int:
    """某个约束“真正起作用”的周期数，例如一天里防倒送限制了多少次。"""
    return sum(1 for a in audits if name in a.binding())


@dataclass
class KpiReport:
    period: str
    values: dict[str, float] = field(default_factory=dict)
    notes: dict[str, str] = field(default_factory=dict)  # 每个 KPI 的口径说明

