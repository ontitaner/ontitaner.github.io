# @AI_GENERATED
"""一次调频专项教材共享基础库。

本模块提供下垂计算、死区处理、限幅裁剪、能力校验、积分电量、考核判定等核心函数。
各章 lab 文件导入本模块，避免重复实现。
所有参数均为教学示例值，不能直接用于现场整定。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
import math
from typing import List, Optional, Sequence, Tuple

FN = 50.0  # 额定频率 (Hz)


class DeadbandMode(str, Enum):
    """死区处理类型。"""
    SHIFT = "shift"   # 连续型 / 平移型
    CUT = "cut"       # 截断型 / 削平型


class FreqRegStatus(str, Enum):
    """一次调频状态机状态。"""
    EXIT = "exit"         # 退出
    ARMED = "armed"       # 投入（频率在死区内）
    ACTIVE = "active"     # 动作（频率越死区）
    BLOCKED = "blocked"   # 闭锁


class BlockReason(str, Enum):
    """闭锁原因。"""
    NONE = "none"
    FREQ_DATA_INVALID = "freq_data_invalid"
    FREQ_DATA_FROZEN = "freq_data_frozen"
    DEVICE_FAULT = "device_fault"
    OVER_RANGE = "over_range"
    MANUAL = "manual"


class IntegrationMode(str, Enum):
    """积分电量计算模式。"""
    EVENT = "event"     # 事件型积分
    PERIOD = "period"   # 周期型积分


@dataclass
class PrimaryFreqConfig:
    """一次调频参数配置（教学示例）。"""
    f_nominal_hz: float = 50.0
    deadband_hz: float = 0.05
    deadband_mode: DeadbandMode = DeadbandMode.CUT
    droop_ratio: float = 0.02
    limit_up_ratio: float = 0.10
    limit_down_ratio: float = 0.20
    p_rated_mw: float = 100.0
    min_output_ratio: float = 0.10
    rocof_deadband_hz_per_s: float = 0.05
    mindwell_s: float = 2.0
    integration_mode: IntegrationMode = IntegrationMode.EVENT
    region: str = ""
    version: str = ""

    @property
    def k(self) -> float:
        """下垂系数 K = Pn / (δ × fn)，单位 MW/Hz。"""
        return self.p_rated_mw / (self.droop_ratio * self.f_nominal_hz)

    @property
    def limit_up_mw(self) -> float:
        return self.limit_up_ratio * self.p_rated_mw

    @property
    def limit_down_mw(self) -> float:
        return self.limit_down_ratio * self.p_rated_mw

    @property
    def min_output_mw(self) -> float:
        return self.min_output_ratio * self.p_rated_mw

    def limit_point_hz(self) -> Tuple[float, float]:
        """达到限幅的频率点（低频侧, 高频侧），半宽偏移。"""
        low = self.f_nominal_hz - (self.deadband_hz + self.limit_up_mw / self.k)
        high = self.f_nominal_hz + (self.deadband_hz + self.limit_down_mw / self.k)
        return low, high


@dataclass
class FreqSample:
    """单次频率采样记录。"""
    ts: float          # 单调时间戳 (s)
    f_hz: float        # 实测频率 (Hz)
    valid: bool = True


@dataclass
class FreqEvent:
    """一次调频事件的完整记录。"""
    event_id: int
    t_start_s: float
    t_end_s: float
    f_hz_series: List[float]
    p_theory_series: List[float]
    p_actual_series: List[float]
    p_exec_series: List[float]
    status_series: List[FreqRegStatus]
    w_theory_mwh: float = 0.0
    w_actual_mwh: float = 0.0
    completion_rate: float = 0.0
    symbol_match: bool = True
    passed: bool = False


@dataclass
class ResourceConfig:
    """单个调频资源的配置。"""
    name: str
    pn_mw: float
    deadband_hz: float
    deadband_mode: DeadbandMode = DeadbandMode.CUT
    droop_ratio: float = 0.03
    limit_up_ratio: float = 0.10
    limit_down_ratio: float = 0.10
    min_output_ratio: float = 0.10
    p_now_mw: float = 0.0
    p_max_mw: float = 0.0

    @property
    def k(self) -> float:
        return self.pn_mw / (self.droop_ratio * FN)

    @property
    def limit_up_mw(self) -> float:
        return self.limit_up_ratio * self.pn_mw

    @property
    def limit_down_mw(self) -> float:
        return self.limit_down_ratio * self.pn_mw

    @property
    def min_output_mw(self) -> float:
        return self.min_output_ratio * self.pn_mw


# ── 核心计算函数 ────────────────────────────────────────────


def deadband_shift(delta_f: float, deadband: float) -> float:
    """连续型（平移型）死区处理。"""
    if abs(delta_f) <= deadband:
        return 0.0
    return delta_f - deadband if delta_f > 0 else delta_f + deadband


def deadband_cut(delta_f: float, deadband: float) -> float:
    """截断型（削平型）死区处理。"""
    return 0.0 if abs(delta_f) <= deadband else delta_f


def apply_deadband(delta_f: float, deadband: float, mode: DeadbandMode) -> float:
    """根据模式选择死区处理函数。"""
    if mode is DeadbandMode.SHIFT:
        return deadband_shift(delta_f, deadband)
    return deadband_cut(delta_f, deadband)


def capability_window(p_now_mw: float, p_max_mw: float,
                      cfg: PrimaryFreqConfig) -> Tuple[float, float]:
    """计算当前可上下调节空间（返回 up, down）。"""
    up = max(0.0, min(p_max_mw - p_now_mw, cfg.limit_up_mw))
    down = max(0.0, min(p_now_mw - cfg.min_output_mw, cfg.limit_down_mw))
    return up, down


def resource_capability_window(r: ResourceConfig) -> Tuple[float, float]:
    """单资源可调空间。"""
    up = max(0.0, min(r.p_max_mw - r.p_now_mw, r.limit_up_mw))
    down = max(0.0, min(r.p_now_mw - r.min_output_mw, r.limit_down_mw))
    return up, down


def primary_freq_delta(f_hz: float, p_now_mw: float, p_max_mw: float,
                       cfg: PrimaryFreqConfig) -> Tuple[float, float]:
    """计算一次调频增量。

    Returns:
        (delta_p_theory_mw, delta_p_exec_mw)
        theory 是按规程口径的理论值，exec 是经能力校验后的可执行值。
    """
    delta_f = f_hz - cfg.f_nominal_hz
    effective = apply_deadband(delta_f, cfg.deadband_hz, cfg.deadband_mode)
    k = cfg.k
    delta_p = -k * effective

    delta_p_theory = max(-cfg.limit_down_mw,
                         min(delta_p, cfg.limit_up_mw))

    up, down = capability_window(p_now_mw, p_max_mw, cfg)
    delta_p_exec = max(-down, min(delta_p_theory, up))
    return delta_p_theory, delta_p_exec


def resource_freq_delta(f_hz: float, r: ResourceConfig) -> Tuple[float, float]:
    """单资源的调频增量计算。"""
    delta_f = f_hz - FN
    effective = apply_deadband(delta_f, r.deadband_hz, r.deadband_mode)
    delta_p = -r.k * effective
    delta_p_theory = max(-r.limit_down_mw, min(delta_p, r.limit_up_mw))
    up, down = resource_capability_window(r)
    delta_p_exec = max(-down, min(delta_p_theory, up))
    return delta_p_theory, delta_p_exec


def multi_resource_synthesis(f_hz: float, resources: List[ResourceConfig]) -> dict:
    """多资源协同合成：每个资源独立计算，求和。"""
    results = {}
    total_theory = 0.0
    total_exec = 0.0
    for r in resources:
        theory, exec_p = resource_freq_delta(f_hz, r)
        results[r.name] = {"theory_mw": theory, "exec_mw": exec_p,
                           "in_deadband": abs(f_hz - FN) <= r.deadband_hz}
        total_theory += theory
        total_exec += exec_p
    results["_total_theory_mw"] = total_theory
    results["_total_exec_mw"] = total_exec
    return results


def integral_energy(theory_mw_series: Sequence[float],
                    actual_mw_series: Sequence[float],
                    dt_s: float,
                    method: str = "trapezoid") -> Tuple[float, float]:
    """计算理论积分电量与实际积分电量。

    Args:
        dt_s: 采样间隔 (s)。
        method: "rect" 矩形法 或 "trapezoid" 梯形法。

    Returns:
        (w_theory_mwh, w_actual_mwh)
    """
    n = min(len(theory_mw_series), len(actual_mw_series))
    if n < 2:
        return 0.0, 0.0
    if method == "rect":
        w_t = sum(abs(p) for p in theory_mw_series[:n]) * dt_s / 3600.0
        w_a = sum(abs(p) for p in actual_mw_series[:n]) * dt_s / 3600.0
    else:
        w_t = 0.0
        w_a = 0.0
        for i in range(n - 1):
            w_t += abs(theory_mw_series[i] + theory_mw_series[i + 1]) / 2.0
            w_a += abs(actual_mw_series[i] + actual_mw_series[i + 1]) / 2.0
        w_t *= dt_s / 3600.0
        w_a *= dt_s / 3600.0
    return w_t, w_a


def assess_event(w_theory_mwh: float, w_actual_mwh: float,
                 completion_threshold: float = 0.60) -> dict:
    """考核判定：两级判断。

    Returns:
        dict with keys: symbol_match, completion_rate, passed, reason
    """
    if w_theory_mwh == 0:
        return {"symbol_match": True, "completion_rate": 1.0,
                "passed": True, "reason": "no_theory_energy"}

    symbol_match = (w_theory_mwh > 0 and w_actual_mwh > 0) or \
                   (w_theory_mwh < 0 and w_actual_mwh < 0) or \
                   (w_actual_mwh == 0)

    completion_rate = abs(w_actual_mwh / w_theory_mwh)

    if not symbol_match:
        return {"symbol_match": False, "completion_rate": completion_rate,
                "passed": False, "reason": "symbol_mismatch"}
    if completion_rate < completion_threshold:
        return {"symbol_match": True, "completion_rate": completion_rate,
                "passed": False, "reason": f"completion_<{completion_threshold:.0%}"}
    return {"symbol_match": True, "completion_rate": completion_rate,
            "passed": True, "reason": "ok"}


def detect_frozen(samples: Sequence[FreqSample], threshold: int = 3) -> bool:
    """检测频率数据是否冻结（连续 N 个采样值不变）。"""
    if len(samples) < threshold:
        return False
    recent = samples[-threshold:]
    return all(s.f_hz == recent[0].f_hz for s in recent)


def rocof_estimate(samples: Sequence[FreqSample]) -> float:
    """滑动窗 df/dt 估计（Hz/s）。"""
    if len(samples) < 2:
        return 0.0
    first, last = samples[0], samples[-1]
    dt = last.ts - first.ts
    if dt <= 0:
        return 0.0
    return (last.f_hz - first.f_hz) / dt


def compute_timing_metrics(
    t_series: Sequence[float],
    f_hz_series: Sequence[float],
    p_series: Sequence[float],
    deadband_hz: float,
    fn: float = 50.0,
    p_target_mw: float | None = None,
    p_stable_band_mw: float = 1.0,
) -> dict:
    """计算 t0.1 / t0.9 / ts 三个时间指标。

    Args:
        t_series: 时间序列 (s)。
        f_hz_series: 频率序列 (Hz)。
        p_series: 出力序列 (MW)。
        deadband_hz: 死区半宽 (Hz)。
        fn: 额定频率。
        p_target_mw: 目标变化量。若为 None 则用理论值。
        p_stable_band_mw: 稳定带宽度 (MW)。

    Returns:
        dict with t0, t01, t09, ts, stable_band_mw, p_initial, p_final_target
    """
    n = len(t_series)
    if n < 2:
        return {}

    # 找 t0：频率首次越过死区
    t0_idx = None
    for i in range(n):
        if abs(f_hz_series[i] - fn) > deadband_hz:
            t0_idx = i
            break
    if t0_idx is None:
        return {}

    t0 = t_series[t0_idx]
    p_initial = p_series[t0_idx]

    if p_target_mw is None:
        p_target_mw = p_series[-1] - p_initial
    if abs(p_target_mw) < 1e-9:
        p_target_mw = 1.0

    p_target_10 = p_initial + 0.10 * p_target_mw
    p_target_90 = p_initial + 0.90 * p_target_mw

    t01 = None
    t09 = None
    ts = None

    for i in range(t0_idx, n):
        p = p_series[i]
        if t01 is None:
            if (p_target_mw > 0 and p >= p_target_10) or \
               (p_target_mw < 0 and p <= p_target_10):
                t01 = t_series[i] - t0
        if t09 is None:
            if (p_target_mw > 0 and p >= p_target_90) or \
               (p_target_mw < 0 and p <= p_target_90):
                t09 = t_series[i] - t0

    # ts：进入稳定带
    p_final_target = p_initial + p_target_mw
    for i in range(t0_idx, n):
        if abs(p_series[i] - p_final_target) <= p_stable_band_mw:
            ts = t_series[i] - t0
            break

    return {
        "t0": t0, "t01_s": t01, "t09_s": t09, "ts_s": ts,
        "p_stable_band_mw": p_stable_band_mw,
        "p_initial_mw": p_initial, "p_target_mw": p_target_mw,
    }


def generate_freq_step(fn: float, step_to_hz: float, step_at_s: float,
                       total_s: float, dt_s: float = 0.1) -> List[FreqSample]:
    """生成频率阶跃信号。"""
    samples = []
    t = 0.0
    while t <= total_s:
        f = step_to_hz if t >= step_at_s else fn
        samples.append(FreqSample(ts=t, f_hz=f))
        t += dt_s
    return samples


def simulate_pcs_response(p_target_series: Sequence[float],
                          delay_s: float, tau_s: float,
                          ramp_rate_mw_per_s: float = 100.0) -> List[float]:
    """模拟 PCS 对指令的响应（一阶+时延+ramp）。

    Args:
        p_target_series: 目标指令序列 (MW 增量)。
        delay_s: 通信与响应时延 (s)。
        tau_s: 一阶时间常数 (s)。
        ramp_rate_mw_per_s: 爬坡速率限制 (MW/s)。

    Returns:
        实际出力序列（与输入等长）。
    """
    n = len(p_target_series)
    actual = [0.0] * n
    delay_steps = max(1, int(delay_s / 0.1))
    for i in range(n):
        if i < delay_steps:
            actual[i] = 0.0
            continue
        target = p_target_series[i - delay_steps]
        prev = actual[i - 1]
        alpha = min(1.0, 0.1 / tau_s) if tau_s > 0 else 1.0
        desired = prev + alpha * (target - prev)
        if abs(desired - prev) > ramp_rate_mw_per_s * 0.1:
            desired = prev + math.copysign(ramp_rate_mw_per_s * 0.1, desired - prev)
        actual[i] = desired
    return actual


class FreqRegStateMachine:
    """一次调频状态机。

    状态转移：
        退出 → 投入（远方投入 + 自检通过）
        投入 → 动作（频率越死区）
        动作 → 投入（频率回死区）
        投入/动作 → 闭锁（异常）
        闭锁 → 投入（异常恢复 + 延时确认）
        任意 → 退出（远方退出）
    """

    def __init__(self, cfg: PrimaryFreqConfig) -> None:
        self.cfg = cfg
        self.status = FreqRegStatus.EXIT
        self.block_reason = BlockReason.NONE
        self._frozen_counter = 0
        self._last_exit_ramp = 0.0
        self._last_f_hz: Optional[float] = None

    def arm(self) -> str:
        if self.status is FreqRegStatus.EXIT:
            self.status = FreqRegStatus.ARMED
            self.block_reason = BlockReason.NONE
            return "armed"
        return f"cannot arm from {self.status.value}"

    def exit(self) -> str:
        self.status = FreqRegStatus.EXIT
        self._last_exit_ramp = 0.0
        return "exited"

    def step(self, sample: FreqSample) -> Tuple[FreqRegStatus, BlockReason]:
        if self.status in (FreqRegStatus.EXIT,):
            return self.status, self.block_reason

        if self.status is FreqRegStatus.BLOCKED:
            return self.status, self.block_reason

        if not sample.valid:
            self.status = FreqRegStatus.BLOCKED
            self.block_reason = BlockReason.FREQ_DATA_INVALID
            return self.status, self.block_reason

        if sample.f_hz < 45.0 or sample.f_hz > 55.0:
            self.status = FreqRegStatus.BLOCKED
            self.block_reason = BlockReason.OVER_RANGE
            return self.status, self.block_reason

        if self._last_f_hz is not None and self._last_f_hz == sample.f_hz:
            self._frozen_counter += 1
            if self._frozen_counter >= 5 and self.status is FreqRegStatus.ACTIVE:
                self.status = FreqRegStatus.BLOCKED
                self.block_reason = BlockReason.FREQ_DATA_FROZEN
                return self.status, self.block_reason
        else:
            self._frozen_counter = 0

        self._last_f_hz = sample.f_hz

        delta_f = abs(sample.f_hz - self.cfg.f_nominal_hz)
        if delta_f > self.cfg.deadband_hz:
            self.status = FreqRegStatus.ACTIVE
        else:
            self.status = FreqRegStatus.ARMED

        return self.status, self.block_reason

    def unblock(self) -> str:
        if self.status is FreqRegStatus.BLOCKED:
            self._frozen_counter = 0
            self.status = FreqRegStatus.ARMED
            self.block_reason = BlockReason.NONE
            return "unblocked → armed"
        return f"not blocked (current: {self.status.value})"


def print_summary(title: str, items: dict) -> None:
    """打印诊断摘要。"""
    print(f"\n{'='*50}")
    print(f"  {title}")
    print(f"{'='*50}")
    for k, v in items.items():
        if isinstance(v, float):
            print(f"  {k:24s}: {v:>12.4f}")
        else:
            print(f"  {k:24s}: {v!s:>12s}")
# @AI_GENERATED: end