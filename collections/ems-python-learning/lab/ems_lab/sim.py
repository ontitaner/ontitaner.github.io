"""第 19 章：EMS 级最小闭环仿真器（以防倒送为例）。

被控对象（Plant）：
- PCS：指令延迟 + 一阶响应 + 额定限幅 + 通信看门狗 + 序号防重放；
- 电池/BMS：按功率积分 SOC（充电乘效率、放电除效率），SOC 接近上下限时线性降额；
- 负荷、光伏：按时间给出的序列（函数）；
- 并网点电表：测量延迟 + 噪声，可注入冻结、过期、失效、丢包；
- 可注入 PCS 拒绝、PCS 离线、BMS 降额、EMS 宕机重启、EMS 墙钟跳变。

控制器（AntiBackfeedEms）：净负荷前馈 + PI 修正求出“防倒送允许的最大放电功率”，
再与 BMS 可充/可放能力一起组成可行域，经 clamp → Ramp → clamp 兜底后下发。

边界：这是 EMS 级离散仿真，只验证控制逻辑、方向、约束、时序和降级；
不验证 PWM、电流环、电磁暂态、真实保护和现场并网性能。全部参数为 [教学示例]/[仿真配置]。
约定（附录 B）：P_BESS 放电为正；P_PCC 向电网送电为正；功率 kW，时间 s，SOC 0～1。
"""
from __future__ import annotations

import math
import random
from bisect import bisect_right
from dataclasses import asdict, dataclass, field
from typing import Callable

from .control import PIController, RateLimiter, clamp, interp_table
from .frequency import PrimaryFrequencyConfig, primary_frequency_power
from .power import pcc_injection_kw

SIM_VERSION = "ems_lab.sim 0.1"
INF = math.inf
Profile = Callable[[float], float]


# ---------------------------------------------------------------- 输入序列
def constant(value: float) -> Profile:
    return lambda t: value


def step_profile(t_step: float, before: float, after: float) -> Profile:
    """t_step 之前取 before，之后取 after：负荷突降、光伏骤升、频率阶跃都用它。"""
    return lambda t: before if t < t_step else after


def steps_profile(points: list[tuple[float, float]]) -> Profile:
    """多段阶跃：points = [(t0, v0), (t1, v1), ...]，按时间升序。"""
    times = [p[0] for p in points]

    def f(t: float) -> float:
        i = bisect_right(times, t) - 1
        return points[max(i, 0)][1]

    return f


# ---------------------------------------------------------------- 故障注入
FAULT_KINDS = {
    "meter_freeze",  # 电表数值冻结，但时标照常刷新（网关缓存旧值的典型表现）
    "meter_stale",  # 电表数据不再更新，时标也停在旧值
    "meter_fail",  # 电表读不到（通信失败）
    "meter_drop",  # 随机丢包，value 为丢包概率
    "pcs_reject",  # PCS 拒绝远方设定（例如切到就地模式），保持原设定
    "pcs_offline",  # PCS 通信中断且停机（功率归零）
    "bms_derate",  # BMS 可放能力降到 value kW
    "clock_jump",  # EMS 墙钟从 t_start 起偏移 value 秒（校时跳变）
    "ems_down",  # EMS 进程宕机，t_end 时重启
}


@dataclass(frozen=True)
class Fault:
    kind: str
    t_start: float
    t_end: float = INF
    value: float = 0.0

    def __post_init__(self):
        if self.kind not in FAULT_KINDS:
            raise ValueError(f"未知故障类型：{self.kind}")

    def active(self, t: float) -> bool:
        return self.t_start <= t < self.t_end


# ---------------------------------------------------------------- 被控对象
@dataclass
class PlantConfig:
    pcs_rated_kw: float = 1000.0
    pcs_delay_s: float = 0.2  # 指令到达 PCS 到开始执行的延迟
    pcs_tau_s: float = 0.3  # PCS 功率一阶响应时间常数
    pcs_watchdog_s: float = 5.0  # 超过此时间收不到 EMS 写入，PCS 设定值回零 [项目配置示例]
    pcs_feedback_error: float = 0.02  # PCS 功率反馈相对并网点电表的偏差（比例）
    capacity_kwh: float = 1000.0
    soc0: float = 0.5
    soc_min: float = 0.10
    soc_max: float = 0.95
    soc_taper: float = 0.05  # 距上下限 5% 内 BMS 线性降额
    soc_trip_margin: float = 0.02  # SOC 越过上下限 2% 视为 BMS 保护动作（用于检出越界）
    eta_ch: float = 0.95
    eta_dis: float = 0.95
    p_aux_kw: float = 20.0  # 站用电（空调、照明）
    loss_ratio: float = 0.01  # PCS 到并网点之间的变压器/线路损耗，按 |P_BESS| 比例近似
    meter_delay_s: float = 0.5
    meter_noise_kw: float = 2.0
    seed: int = 7


@dataclass(frozen=True)
class MeterReading:
    p_pcc_kw: float
    sample_time: float  # 采样时刻（采集网关时钟）


@dataclass(frozen=True)
class PcsFeedback:
    p_kw: float
    remote: bool  # True：远方模式，接受 EMS 设定


@dataclass(frozen=True)
class Ack:
    accepted: bool
    reason: str = ""


class Plant:
    def __init__(self, cfg: PlantConfig, faults: list[Fault]):
        self.cfg = cfg
        self.faults = faults
        self.rng = random.Random(cfg.seed)
        self.soc = cfg.soc0
        self.p_actual = 0.0
        self.setpoint = 0.0
        self.pending: list[tuple[float, float]] = []  # (生效时刻, 设定值)
        self.last_seq = 0
        self.last_contact_t = 0.0
        self.bms_tripped = False
        self._mt: list[float] = []  # 电表历史：时刻
        self._mv: list[float] = []  # 电表历史：真实 P_PCC
        self._frozen: MeterReading | None = None
        self._stale: MeterReading | None = None

    def fault(self, kind: str, t: float) -> Fault | None:
        for f in self.faults:
            if f.kind == kind and f.active(t):
                return f
        return None

    # ---- BMS
    def bms_caps(self, t: float) -> tuple[float, float]:
        """返回 (可充, 可放) 非负幅值。SOC 靠近下限时可放线性降到 0，靠近上限时可充降到 0。"""
        c = self.cfg
        if self.bms_tripped:
            return 0.0, 0.0
        dis = c.pcs_rated_kw * interp_table(self.soc, [c.soc_min, c.soc_min + c.soc_taper], [0.0, 1.0])
        ch = c.pcs_rated_kw * interp_table(self.soc, [c.soc_max - c.soc_taper, c.soc_max], [1.0, 0.0])
        f = self.fault("bms_derate", t)
        if f is not None:
            dis = min(dis, f.value)
        return ch, dis

    # ---- PCS
    def read_pcs(self, t: float) -> PcsFeedback | None:
        if self.fault("pcs_offline", t):
            return None
        remote = self.fault("pcs_reject", t) is None
        return PcsFeedback(self.p_actual * (1.0 + self.cfg.pcs_feedback_error), remote)

    def write_pcs(self, t: float, setpoint_kw: float, seq: int) -> Ack:
        if self.fault("pcs_offline", t):
            return Ack(False, "无应答")
        self.last_contact_t = t  # 看门狗：只要通信在，就算“有联系”
        if self.fault("pcs_reject", t):
            return Ack(False, "PCS 处于就地模式，拒绝远方设定")
        if seq <= self.last_seq:
            return Ack(False, f"序号 {seq} 不大于已执行序号 {self.last_seq}，按旧命令拒绝")
        self.last_seq = seq
        r = self.cfg.pcs_rated_kw
        self.pending.append((t + self.cfg.pcs_delay_s, clamp(setpoint_kw, -r, r)))
        return Ack(True)

    # ---- 电表
    def read_meter(self, t: float) -> MeterReading | None:
        if self.fault("meter_fail", t):
            return None
        drop = self.fault("meter_drop", t)
        if drop is not None and self.rng.random() < drop.value:
            return None
        i = bisect_right(self._mt, t - self.cfg.meter_delay_s) - 1
        if i < 0:
            return None  # 刚启动，还没有足够旧的样本
        reading = MeterReading(self._mv[i] + self.rng.gauss(0.0, self.cfg.meter_noise_kw), self._mt[i])
        if self.fault("meter_freeze", t):
            if self._frozen is None:
                self._frozen = reading
            return MeterReading(self._frozen.p_pcc_kw, reading.sample_time)  # 数值不变，时标在走
        self._frozen = None
        if self.fault("meter_stale", t):
            if self._stale is None:
                self._stale = reading
            return self._stale  # 数值和时标都停在旧值
        self._stale = None
        return reading

    # ---- 物理推进一步
    def step(self, t: float, dt: float, p_load_kw: float, p_pv_kw: float) -> float:
        c = self.cfg
        while self.pending and self.pending[0][0] <= t:
            self.setpoint = self.pending.pop(0)[1]
        if t - self.last_contact_t > c.pcs_watchdog_s:
            self.setpoint = 0.0  # PCS 通信看门狗
        if self.fault("pcs_offline", t) or self.bms_tripped:
            self.setpoint, self.p_actual = 0.0, 0.0
            self.pending.clear()
        self.p_actual += (self.setpoint - self.p_actual) * min(1.0, dt / c.pcs_tau_s)

        # 电池：放电除效率，充电乘效率（第 05 章）
        if self.p_actual > 0:
            self.soc -= self.p_actual / c.eta_dis * dt / 3600.0 / c.capacity_kwh
        else:
            self.soc += -self.p_actual * c.eta_ch * dt / 3600.0 / c.capacity_kwh
        if self.soc < c.soc_min - c.soc_trip_margin or self.soc > c.soc_max + c.soc_trip_margin:
            self.bms_tripped = True

        p_loss = c.loss_ratio * abs(self.p_actual)
        p_pcc = pcc_injection_kw(self.p_actual, p_load_kw, c.p_aux_kw, p_loss, p_pv_kw)
        self._mt.append(t)
        self._mv.append(p_pcc)
        return p_pcc


# ---------------------------------------------------------------- EMS 控制器
@dataclass
class EmsConfig:
    cycle_s: float = 0.2
    export_limit_kw: float = 0.0  # 并网协议：不允许倒送
    import_margin_kw: float = 30.0  # 控制目标保留 30 kW 取电裕量
    ramp_up_kw_s: float = 100.0
    ramp_down_kw_s: float = 100.0
    kp: float = 0.1
    ki: float = 0.3
    trim_max_kw: float = 100.0  # PI 修正量的权限上限
    i_separation_kw: float = 50.0  # 偏差超过此值时暂停积分（积分分离）
    meter_stale_s: float = 2.0
    meter_frozen_s: float = 3.0
    meter_frozen_tol_kw: float = 0.05
    meter_recover_s: float = 2.0  # 电表恢复后需连续可信这么久才退出降级
    track_error_kw: float = 50.0
    track_error_s: float = 2.0
    dt_max_s: float = 1.0
    use_monotonic: bool = True  # 周期 dt 与数据年龄用单调时钟；墙钟只写进记录
    align_timestamps: bool = True  # 前馈用“与电表采样同一时刻”的 PCS 反馈
    sync_on_reject: bool = True  # PCS 拒绝时把 Ramp 状态同步到实测
    config_version: str = "cfg-demo-1"


@dataclass
class Decision:
    t: float  # 单调时间
    t_wall: float  # 墙钟（记录用）
    seq: int
    request_kw: float
    lower_kw: float
    upper_kw: float
    final_kw: float
    binding: list[str]
    meter_quality: str
    degraded: bool
    accepted: bool | None = None
    ramp_after_ack_kw: float | None = None


class AntiBackfeedEms:
    def __init__(self, cfg: EmsConfig, pfr: PrimaryFrequencyConfig | None = None):
        self.cfg = cfg
        self.pfr = pfr
        self.ramp = RateLimiter(cfg.ramp_up_kw_s, cfg.ramp_down_kw_s)
        # PI 输出范围放开：可行域和冲突检测由下面的流水线显式处理
        self.pi = PIController(cfg.kp, cfg.ki, -1e9, 1e9, anti_windup=False)
        self.seq = 0
        self.last_t: float | None = None
        self.last_final = 0.0
        self.backfeed_active = False
        self.degraded = True  # 上电/重启先降级，等电表连续可信再闭环
        self.meter_ever_good = False
        self.good_since: float | None = None
        self.last_meter: MeterReading | None = None
        self.frozen_ref: tuple[float, float] | None = None  # (参考值, 参考时刻)
        self.pcs_hist: list[tuple[float, float]] = []
        self.track_timer = 0.0
        self.meter_comm_failures = 0
        self.alarms: set[str] = set()
        self.events: list[tuple[float, str, str]] = []  # (时刻, "+"/"-", 告警码)

    # ---- 告警（完整生命周期见第 20 章 observability.py）
    def _alarm(self, t: float, code: str, on: bool) -> None:
        if on and code not in self.alarms:
            self.alarms.add(code)
            self.events.append((t, "+", code))
        elif not on and code in self.alarms:
            self.alarms.discard(code)
            self.events.append((t, "-", code))

    def recover(self, p_actual_kw: float, last_seq: int, trust_old_state: bool = False) -> None:
        """重启恢复：Ramp 从实测功率起步，序号接着持久化的值，积分清零，重新确认数据。

        trust_old_state=True 是反例：把“旧快照”当作现在（直接按旧功率继续、不重新确认数据）。
        """
        self.ramp.reset(p_actual_kw)
        self.last_final = p_actual_kw
        self.seq = last_seq
        self.pi.reset()
        if trust_old_state:
            self.degraded = False
            self.meter_ever_good = True

    # ---- 电表质量
    def _meter_quality(self, now: float, m: MeterReading | None) -> str:
        c = self.cfg
        if m is None:
            self.meter_comm_failures += 1
        else:
            if self.frozen_ref is None or abs(m.p_pcc_kw - self.frozen_ref[0]) > c.meter_frozen_tol_kw:
                self.frozen_ref = (m.p_pcc_kw, m.sample_time)
            self.last_meter = m
        last = self.last_meter
        if last is None:
            return "COMM_FAILED"
        age = now - last.sample_time
        if age < -1.0:
            return "INVALID"  # 时标在未来：时钟有问题
        if age > c.meter_stale_s:
            return "STALE"
        if last.sample_time - self.frozen_ref[1] >= c.meter_frozen_s:
            return "FROZEN"
        return "GOOD"

    def _p_bess_at(self, t_sample: float) -> float:
        """取电表采样时刻对应的 PCS 反馈，保证功率平衡两边来自同一时刻。"""
        if not self.cfg.align_timestamps or not self.pcs_hist:
            return self.pcs_hist[-1][1] if self.pcs_hist else 0.0
        times = [h[0] for h in self.pcs_hist]
        i = bisect_right(times, t_sample) - 1
        return self.pcs_hist[max(i, 0)][1]

    # ---- 一个控制周期
    def step(
        self,
        now_mono: float,
        now_wall: float,
        meter: MeterReading | None,
        pcs: PcsFeedback | None,
        caps: tuple[float, float] | None,
        p_request_kw: float,
        f_hz: float | None = None,
    ) -> Decision:
        c = self.cfg
        now = now_mono if c.use_monotonic else now_wall
        binding: list[str] = []  # 真正把请求“压下来”的约束，以及异常说明（审计用）

        # 1) 周期间隔保护：时钟跳变或调度卡顿时 dt 异常，按标称周期计算
        dt = c.cycle_s if self.last_t is None else now - self.last_t
        dt_bad = dt <= 0 or dt > c.dt_max_s
        self._alarm(now, "CLOCK_DT", dt_bad)
        if dt_bad:
            dt = c.cycle_s
        self.last_t = now

        # 2) 设备数据：PCS 离线 → 能力置 0；BMS 无数据 → 能力置 0
        self._alarm(now, "PCS_OFFLINE", pcs is None)
        if pcs is not None:
            self.pcs_hist.append((now, pcs.p_kw))
            self.pcs_hist = self.pcs_hist[-200:]
            err = abs(self.last_final - pcs.p_kw)
            self.track_timer = self.track_timer + dt if err > c.track_error_kw else 0.0
            tracking_bad = self.track_timer >= c.track_error_s
            self._alarm(now, "PCS_TRACK", tracking_bad)
            if tracking_bad:
                self.ramp.reset(pcs.p_kw)
        avail_ch, avail_dis = caps if caps is not None else (0.0, 0.0)
        if pcs is None:
            avail_ch = avail_dis = 0.0
            binding.append("PCS 离线：能力置 0")

        # 3) 电表质量与降级（带恢复保持时间，防止来回切换）
        q = self._meter_quality(now, meter)
        if q == "GOOD":
            self.good_since = now if self.good_since is None else self.good_since
            if self.degraded and now - self.good_since >= c.meter_recover_s:
                self.degraded = False
                self.pi.reset()
            self.meter_ever_good = True
        else:
            self.good_since = None
            if not self.degraded:
                self.pi.reset()
            self.degraded = True
        self._alarm(now, "METER_BAD", q != "GOOD" and self.meter_ever_good)

        # 4) 请求：策略请求 + 一次调频增量（第 15 章）
        request = p_request_kw
        if self.pfr is not None and f_hz is not None:
            request += primary_frequency_power(f_hz, self.pfr)

        # 5) 防倒送上限：净负荷前馈 + PI 修正；电表不可信时禁止放电
        lower, upper, upper_src = -avail_ch, avail_dis, "可放能力"
        target_pcc = c.export_limit_kw - c.import_margin_kw
        if self.degraded:
            bound, bound_src = 0.0, f"电表{q}：防倒送降级，禁止放电"
        else:
            m = self.last_meter
            ff = (self._p_bess_at(m.sample_time) - m.p_pcc_kw) + target_pcc  # 净负荷估计 + 目标
            e = target_pcc - m.p_pcc_kw
            # 只在约束起作用、且偏差不大时积分：
            # 约束不起作用时积分会在“看不见的地方”积累；偏差大多半是延迟造成的暂态，不是稳态偏差（积分分离）
            integrate = (self.backfeed_active or e < 0) and abs(e) <= c.i_separation_kw
            saved = self.pi.integral
            bound = self.pi.update(e, dt, feedforward=ff)
            if not integrate:
                self.pi.integral = saved
            self.pi.integral = clamp(self.pi.integral, -c.trim_max_kw, c.trim_max_kw)
            bound_src = "防倒送"
        if bound < upper:
            upper, upper_src = bound, bound_src
        infeasible = upper < lower
        if infeasible:
            binding.append("可行域为空：需要的充电超过可充能力，应请求光伏限发")
            upper = lower
        self._alarm(now, "FEASIBLE_EMPTY", infeasible)

        # 6) clamp → Ramp → clamp 兜底（第 11 章）
        if request > upper:
            binding.append(upper_src)
        elif request < lower:
            binding.append("可充能力")
        target = clamp(request, lower, upper)
        ramped = self.ramp.update(target, dt)
        final = clamp(ramped, lower, upper)
        if final != ramped:
            self.ramp.reset(final)
        elif final != target:
            binding.append("Ramp")
        self.backfeed_active = request > upper and upper_src == "防倒送"

        self.seq += 1
        self.last_final = final
        return Decision(now_mono, now_wall, self.seq, request, lower, upper, final, binding, q, self.degraded)

    def on_ack(self, t: float, ack: Ack, pcs: PcsFeedback | None) -> None:
        """设备不接受时不假设成功：告警，并把 Ramp 状态拉回实测值。"""
        self._alarm(t, "PCS_REJECT", not ack.accepted and pcs is not None)
        if not ack.accepted and pcs is not None and self.cfg.sync_on_reject:
            self.ramp.reset(pcs.p_kw)
            self.last_final = pcs.p_kw


# ---------------------------------------------------------------- 场景与运行
@dataclass
class Scenario:
    name: str
    t_end_s: float = 30.0
    dt_s: float = 0.05
    load_kw: Profile = field(default_factory=lambda: constant(800.0))
    pv_kw: Profile = field(default_factory=lambda: constant(0.0))
    request_kw: Profile = field(default_factory=lambda: constant(600.0))  # 经济策略的放电请求
    freq_hz: Profile | None = None
    plant: PlantConfig = field(default_factory=PlantConfig)
    ems: EmsConfig = field(default_factory=EmsConfig)
    pfr: PrimaryFrequencyConfig | None = None
    faults: list[Fault] = field(default_factory=list)
    replay_on_restart: bool = False  # 反例：重启后按旧快照继续


@dataclass
class Trace:
    scenario: Scenario
    t: list[float] = field(default_factory=list)
    p_load: list[float] = field(default_factory=list)
    p_pv: list[float] = field(default_factory=list)
    p_bess: list[float] = field(default_factory=list)  # PCS 实际功率（真实值）
    p_cmd: list[float] = field(default_factory=list)  # EMS 最近一次下发值
    p_pcc: list[float] = field(default_factory=list)  # 并网点真实功率
    p_pcc_seen: list[float] = field(default_factory=list)  # EMS 看到的并网点功率
    soc: list[float] = field(default_factory=list)
    avail_ch: list[float] = field(default_factory=list)
    avail_dis: list[float] = field(default_factory=list)
    p_loss: list[float] = field(default_factory=list)
    decisions: list[Decision] = field(default_factory=list)
    events: list[tuple[float, str, str]] = field(default_factory=list)
    bms_tripped: bool = False
    meter_comm_failures: int = 0


def run(scn: Scenario) -> Trace:
    plant = Plant(scn.plant, scn.faults)
    ems = AntiBackfeedEms(scn.ems, scn.pfr)
    tr = Trace(scn)
    n = int(round(scn.t_end_s / scn.dt_s))
    next_cycle = 0.0
    alive = True
    persisted_seq = 0
    fails_before = 0
    for k in range(n + 1):
        t = k * scn.dt_s
        offset = sum(f.value for f in scn.faults if f.kind == "clock_jump" and t >= f.t_start)

        if plant.fault("ems_down", t):
            if alive:
                tr.events += ems.events
                fails_before += ems.meter_comm_failures
                ems.events = []
            alive = False
            next_cycle = t
        elif not alive:  # 重启
            fb = plant.read_pcs(t)
            old_final = ems.last_final
            ems = AntiBackfeedEms(scn.ems, scn.pfr)
            if scn.replay_on_restart:
                ems.recover(old_final, persisted_seq, trust_old_state=True)
            else:
                ems.recover(fb.p_kw if fb else 0.0, persisted_seq)
            ems.events.append((t, "+", "EMS_RESTART"))
            alive = True

        if alive and t >= next_cycle - 1e-9:
            next_cycle += scn.ems.cycle_s
            meter = plant.read_meter(t)
            fb = plant.read_pcs(t)
            f_hz = scn.freq_hz(t) if scn.freq_hz else None
            d = ems.step(t, t + offset, meter, fb, plant.bms_caps(t), scn.request_kw(t), f_hz)
            ack = plant.write_pcs(t, d.final_kw, d.seq)
            ems.on_ack(t, ack, fb)
            d.accepted = ack.accepted
            d.ramp_after_ack_kw = ems.ramp.output
            persisted_seq = d.seq
            tr.decisions.append(d)

        ch, dis = plant.bms_caps(t)
        p_pcc = plant.step(t, scn.dt_s, scn.load_kw(t), scn.pv_kw(t))
        tr.t.append(t)
        tr.p_load.append(scn.load_kw(t))
        tr.p_pv.append(scn.pv_kw(t))
        tr.p_bess.append(plant.p_actual)
        tr.p_cmd.append(tr.decisions[-1].final_kw if tr.decisions else 0.0)
        tr.p_pcc.append(p_pcc)
        tr.p_pcc_seen.append(ems.last_meter.p_pcc_kw if ems.last_meter else math.nan)
        tr.soc.append(plant.soc)
        tr.avail_ch.append(ch)
        tr.avail_dis.append(dis)
        tr.p_loss.append(scn.plant.loss_ratio * abs(plant.p_actual))
    tr.events += ems.events
    tr.bms_tripped = plant.bms_tripped
    tr.meter_comm_failures = fails_before + ems.meter_comm_failures
    return tr


# ---------------------------------------------------------------- 断言工具：带容差和持续时间
def longest_excursion_s(t: list[float], x: list[float], limit: float, tol: float = 0.0) -> float:
    """x 连续超过 (limit + tol) 的最长持续时间。“超一下”和“持续超”在现场是两回事。"""
    longest, start = 0.0, None
    for ti, xi in zip(t, x):
        if xi > limit + tol:
            start = ti if start is None else start
            longest = max(longest, ti - start)
        else:
            start = None
    return longest


def window(t: list[float], x: list[float], t0: float, t1: float = INF) -> list[float]:
    return [xi for ti, xi in zip(t, x) if t0 <= ti < t1]


def max_rise_rate_kw_s(decisions: list[Decision], t0: float = 0.0, t1: float = INF) -> float:
    """相邻两次下发之间的最大上升速率（按单调时间计算）。"""
    ds = [d for d in decisions if t0 <= d.t < t1]
    rates = [(b.final_kw - a.final_kw) / (b.t - a.t) for a, b in zip(ds, ds[1:]) if b.t > a.t]
    return max(rates, default=0.0)


def max_rate_over_window_kw_s(t: list[float], x: list[float], window_s: float, t0: float = 0.0) -> float:
    """实际功率在 window_s 窗口内的最大平均上升速率。

    阶梯状指令 + 一阶响应，瞬时斜率会超过 Ramp 设定；验收时 Ramp 按规定窗口计算，断言也要写明窗口。
    """
    dt = t[1] - t[0]
    n = max(1, int(round(window_s / dt)))
    rates = [(x[i + n] - x[i]) / (t[i + n] - t[i]) for i in range(len(t) - n) if t[i] >= t0]
    return max(rates, default=0.0)


def power_balance_residual_kw(tr: Trace) -> float:
    """记录的各项是否满足 P_PCC = P_PV + P_BESS − P_load − P_aux − P_loss（查模型和记录字段有没有错位）。"""
    aux = tr.scenario.plant.p_aux_kw
    return max(
        abs(pcc - pcc_injection_kw(b, ld, aux, loss, pv))
        for pcc, b, ld, loss, pv in zip(tr.p_pcc, tr.p_bess, tr.p_load, tr.p_loss, tr.p_pv)
    )


def first_event_time(events: list[tuple[float, str, str]], code: str, sign: str = "+") -> float | None:
    for t, s, c in events:
        if c == code and s == sign:
            return t
    return None


@dataclass
class Check:
    name: str
    expression: str  # PASS 表达式，写成人能复核的形式
    value: float
    threshold: float
    passed: bool


def check_le(name: str, value: float, threshold: float, expression: str) -> Check:
    return Check(name, expression, value, threshold, value <= threshold)


def evidence(tr: Trace, checks: list[Check]) -> dict:
    """测试结果即证据：场景、参数、版本、故障、每条断言的表达式与实测值、总结论。"""
    s = tr.scenario
    return {
        "scenario": s.name,
        "sim_version": SIM_VERSION,
        "config_version": s.ems.config_version,
        "plant": asdict(s.plant),
        "ems": asdict(s.ems),
        "faults": [asdict(f) for f in s.faults],
        "checks": [asdict(c) for c in checks],
        "verdict": "PASS" if all(c.passed for c in checks) else "FAIL",
    }

