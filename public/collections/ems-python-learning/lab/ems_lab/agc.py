"""第 16 章：AGC（二次调频）——ACE、设点接收、跟踪仿真与教学版考核指标。

约定：功率 kW，放电为正、充电为负；时间 s；SOC 0~1。
考核指标的定义、阈值和综合公式均为 [教学示例]，现场以国家能源局《电力并网运行管理规定》
《电力辅助服务管理办法》及所在区域/省级实施细则为准。
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Sequence

import numpy as np

from .control import RateLimiter, clamp, limit_then_ramp


# ================================================================ ACE
def ace_mw(delta_p_tie_mw: float, delta_f_hz: float, bias_mw_per_hz: float) -> float:
    """区域控制偏差 ACE = ΔP_tie + B·Δf（本课程采用的一种常见形式）。

    - ΔP_tie = 联络线实际净送出 − 计划净送出，**送出为正**；
    - Δf = 实测频率 − 额定频率；
    - B：频率偏差系数（MW/Hz），本函数取**正数**。
    ACE > 0：本区域发电偏多；ACE < 0：本区域发电偏少。本区域需要增加的发电 = −ACE。
    注意：不同电网/教材的符号约定不同（例如 B 取负数、写成 ΔP_tie − 10B·Δf），接入前必须核对。
    """
    if bias_mw_per_hz <= 0:
        raise ValueError("本函数约定 B 为正数（MW/Hz）")
    return delta_p_tie_mw + bias_mw_per_hz * delta_f_hz


# ================================================================ 遥调量解码
def decode_scaled(raw: float, scale: float, offset: float = 0.0) -> float:
    """标度化值 → 工程值：工程值 = 原始值 × 系数 + 偏移。系数、单位来自点表，必须配置化。"""
    return raw * scale + offset


def decode_normalized(raw_norm: float, full_scale_kw: float) -> float:
    """归一化值（IEC 104 归一化设点，范围约 −1～+1）→ 工程值：归一化值 × 满量程。

    满量程填错（例如填了单台 PCS 容量而不是全站容量）会让所有指令按比例缩放。
    """
    if not -1.0 <= raw_norm <= 1.0:
        raise ValueError(f"归一化值越界：{raw_norm}")
    return raw_norm * full_scale_kw


# ================================================================ 设点接收与校验
@dataclass
class AgcReceiverConfig:
    p_min_kw: float  # 允许的最小设点（充电方向为负）
    p_max_kw: float  # 允许的最大设点（放电方向为正）
    max_age_s: float = 30.0  # 指令时标允许的最大“年龄” [教学示例]
    hold_s: float = 60.0  # 通信中断/指令失效后保持上一有效值的时长 [教学示例]


@dataclass(frozen=True)
class AgcSetpoint:
    p_kw: float
    status: str  # ACCEPTED / HOLD / FALLBACK / AGC_OFF
    reason: str


class AgcReceiver:
    """接收调度 AGC 设点：校验 → 接受 / 保持上一有效值 / 回退计划。

    失效处理（保持多久、回退到什么）必须按调度规程和并网调度协议配置，这里只演示结构。
    """

    def __init__(self, cfg: AgcReceiverConfig):
        if cfg.p_min_kw > cfg.p_max_kw:
            raise ValueError("p_min_kw 不能大于 p_max_kw")
        self.cfg = cfg
        self.last_valid_kw: float | None = None
        self.last_valid_at: float | None = None

    def _hold_or_fallback(self, now: float, schedule_kw: float, why: str) -> AgcSetpoint:
        if self.last_valid_kw is not None and self.last_valid_at is not None and now - self.last_valid_at <= self.cfg.hold_s:
            return AgcSetpoint(self.last_valid_kw, "HOLD", f"{why}：保持上一有效值")
        return AgcSetpoint(schedule_kw, "FALLBACK", f"{why}：超过保持时长，回退计划")

    def update(
        self,
        now: float,
        value_kw: float | None,
        stamp_s: float | None,
        link_ok: bool = True,
        agc_enabled: bool = True,
        schedule_kw: float = 0.0,
    ) -> AgcSetpoint:
        if not agc_enabled:
            return AgcSetpoint(schedule_kw, "AGC_OFF", "AGC 未投入：跟踪计划")
        if not link_ok or value_kw is None:
            return self._hold_or_fallback(now, schedule_kw, "调度通道中断")
        if isinstance(value_kw, float) and math.isnan(value_kw):
            return self._hold_or_fallback(now, schedule_kw, "设点为 NaN")
        if stamp_s is None or now - stamp_s > self.cfg.max_age_s:
            # “寄存器在刷新”不等于“指令是新的”：以指令时标/通道状态判断
            return self._hold_or_fallback(now, schedule_kw, "指令时标过旧")
        if not self.cfg.p_min_kw <= value_kw <= self.cfg.p_max_kw:
            return self._hold_or_fallback(now, schedule_kw, f"设点 {value_kw:.0f} kW 越量程")
        self.last_valid_kw, self.last_valid_at = value_kw, now
        return AgcSetpoint(value_kw, "ACCEPTED", "有效设点")


# ================================================================ 上送可调能力
def regulation_capability(
    soc: float,
    energy_kwh: float,
    p_discharge_avail_kw: float,
    p_charge_avail_kw: float,
    soc_min: float = 0.10,
    soc_max: float = 0.90,
    sustain_h: float = 0.25,
) -> tuple[float, float]:
    """可调上限（放电方向，正数）与可调下限（充电方向，负数）。

    同时受功率能力和“能以该功率持续 sustain_h 小时”的电量约束。
    sustain_h、SOC 上下限为 [教学示例]，以调度要求和项目配置为准。
    """
    if energy_kwh <= 0 or sustain_h <= 0:
        raise ValueError("容量和持续时间必须为正")
    if p_discharge_avail_kw < 0 or p_charge_avail_kw < 0:
        raise ValueError("可充/可放能力必须是非负幅值")
    up_energy = max(0.0, soc - soc_min) * energy_kwh / sustain_h
    down_energy = max(0.0, soc_max - soc) * energy_kwh / sustain_h
    return min(p_discharge_avail_kw, up_energy), -min(p_charge_avail_kw, down_energy)


# ================================================================ 跟踪仿真
@dataclass
class StationModel:
    """储能站（或火电机组）对 AGC 设点的教学响应模型：通信延迟 + Ramp + 一阶惯性。"""

    p_rated_kw: float
    ramp_kw_per_s: float
    tau_s: float = 1.0  # 执行一阶惯性时间常数，0 表示无惯性
    delay_s: float = 2.0  # 调度下发 → 站内开始执行的延迟（通信 + EMS 周期）
    offset_kw: float = 0.0  # 稳态偏差（例如考核点在并网点，站用电/损耗未补偿）
    energy_kwh: float | None = None  # None 表示不受电量限制（例如火电）
    soc0: float = 0.5
    soc_min: float = 0.05
    soc_max: float = 0.95
    p_min_kw: float | None = None  # 最小出力（火电为最低稳燃负荷），None 表示 −p_rated


@dataclass
class TrackingResult:
    t: np.ndarray
    p_cmd: np.ndarray  # 调度下发的设点（未经延迟）
    p_act: np.ndarray  # 考核点实际出力
    soc: np.ndarray


def command_at(commands: Sequence[tuple[float, float]], t: float, p0_kw: float = 0.0) -> float:
    """阶梯设点序列在 t 时刻的值。commands 为 [(时刻, 设点)]，按时间递增。"""
    p = p0_kw
    for tc, pc in commands:
        if t >= tc:
            p = pc
        else:
            break
    return p


def simulate_tracking(
    commands: Sequence[tuple[float, float]],
    model: StationModel,
    t_end_s: float,
    dt: float = 0.1,
    p0_kw: float = 0.0,
) -> TrackingResult:
    n = int(round(t_end_s / dt)) + 1
    t = np.arange(n) * dt
    p_cmd, p_act, soc_arr = np.zeros(n), np.zeros(n), np.zeros(n)
    ramp = RateLimiter(model.ramp_kw_per_s, model.ramp_kw_per_s, initial=p0_kw)
    p_exec = p0_kw  # 执行端实际功率（不含偏差）
    soc = model.soc0
    p_lo_rated = -model.p_rated_kw if model.p_min_kw is None else model.p_min_kw
    for k in range(n):
        p_cmd[k] = command_at(commands, t[k], p0_kw)
        seen = command_at(commands, t[k] - model.delay_s, p0_kw)  # 延迟后才“看到”新设点
        # 可充/可放能力：SOC 到限就归零（真实系统由 BMS 给出，且会提前降额）
        dis_cap = model.p_rated_kw
        chg_cap = -p_lo_rated if p_lo_rated < 0 else 0.0
        if model.energy_kwh is not None:
            if soc <= model.soc_min:
                dis_cap = 0.0
            if soc >= model.soc_max:
                chg_cap = 0.0
        if p_lo_rated >= 0:  # 火电：只能在 [最小出力, 额定] 之间
            target = ramp.update(clamp(seen, p_lo_rated, model.p_rated_kw), dt)
        else:
            target = limit_then_ramp(seen, ramp, dt, chg_cap, dis_cap)
        if model.tau_s > 0:
            p_exec += (target - p_exec) * min(1.0, dt / model.tau_s)
        else:
            p_exec = target
        if model.energy_kwh is not None:
            soc -= p_exec * dt / 3600.0 / model.energy_kwh
            soc = min(max(soc, 0.0), 1.0)
        p_act[k] = p_exec + model.offset_kw
        soc_arr[k] = soc
    return TrackingResult(t, p_cmd, p_act, soc_arr)


# ================================================================ 教学版考核指标
@dataclass
class StepMetrics:
    t_cmd_s: float
    p_start_kw: float
    p_target_kw: float
    response_time_s: float | None  # 下发 → 出力朝目标方向离开起点带
    reach_time_s: float | None  # 下发 → 出力进入目标带
    rate_kw_per_s: float | None  # 离开起点带到进入目标带之间的平均速率
    accuracy_kw: float | None  # 进入目标带后 |实际 − 设点| 的平均值
    reached: bool
    notes: list[str] = field(default_factory=list)


def evaluate_step(
    t: np.ndarray,
    p_act: np.ndarray,
    t_cmd_s: float,
    t_next_s: float,
    p_start_kw: float,
    p_target_kw: float,
    band_kw: float,
) -> StepMetrics:
    """对一次设点变化计算响应时间、调节速率、调节精度。定义均为 [教学示例]。"""
    if band_kw <= 0:
        raise ValueError("判定带宽必须为正")
    mask = (t >= t_cmd_s) & (t < t_next_s)
    ts, ps = t[mask], p_act[mask]
    direction = 1.0 if p_target_kw >= p_start_kw else -1.0
    notes: list[str] = []
    left = np.where((ps - p_start_kw) * direction >= band_kw)[0]
    reach = np.where(np.abs(ps - p_target_kw) <= band_kw)[0]
    t_resp = float(ts[left[0]] - t_cmd_s) if left.size else None
    t_reach = float(ts[reach[0]] - t_cmd_s) if reach.size else None
    rate = None
    if left.size and reach.size and reach[0] > left[0]:
        rate = abs(float(ps[reach[0]] - ps[left[0]])) / float(ts[reach[0]] - ts[left[0]])
    if reach.size:
        acc = float(np.mean(np.abs(ps[reach[0]:] - p_target_kw)))
    else:
        notes.append("未进入目标带：按后半段偏差计精度")
        half = ps[len(ps) // 2:]
        acc = float(np.mean(np.abs(half - p_target_kw))) if half.size else None
    if t_resp is None:
        notes.append("出力未朝目标方向变化")
    return StepMetrics(t_cmd_s, p_start_kw, p_target_kw, t_resp, t_reach, rate, acc, bool(reach.size), notes)


def performance_index(
    m: StepMetrics,
    rate_std_kw_per_s: float,
    t_std_s: float,
    err_allow_kw: float,
    k1_max: float = 5.0,
) -> dict[str, float]:
    """[教学示例] 综合调频性能指标：k1（速率）× k2（精度）× k3（响应时间）。

    各地细则的分项定义、归一化基准、上下限和合成方式都不同，这里只演示“多个分项合成一个系数”的思路。
    """
    k1 = 0.0 if m.rate_kw_per_s is None else min(m.rate_kw_per_s / rate_std_kw_per_s, k1_max)
    k2 = 0.0 if m.accuracy_kw is None else max(0.0, 1.0 - m.accuracy_kw / err_allow_kw)
    k3 = 0.0 if m.response_time_s is None else max(0.0, 1.0 - m.response_time_s / t_std_s)
    return {"k1": k1, "k2": k2, "k3": k3, "kp": k1 * k2 * k3}


# ================================================================ 火储联合【了解】
def simulate_thermal_bess(
    commands: Sequence[tuple[float, float]],
    thermal: StationModel,
    bess: StationModel,
    t_end_s: float,
    dt: float = 0.1,
    p0_kw: float = 0.0,
) -> tuple[TrackingResult, np.ndarray, np.ndarray]:
    """火储联合调频（教学简化）：机组按原速率跟踪，储能补“设点 − 机组出力”的差额。

    返回 (机组跟踪结果, 储能出力, 联合出力)。储能出力受额定功率、Ramp、SOC 约束。
    """
    th = simulate_tracking(commands, thermal, t_end_s, dt, p0_kw)
    n = th.t.size
    p_b, total = np.zeros(n), np.zeros(n)
    ramp = RateLimiter(bess.ramp_kw_per_s, bess.ramp_kw_per_s)
    soc, p_exec = bess.soc0, 0.0
    e = bess.energy_kwh if bess.energy_kwh is not None else math.inf
    for k in range(n):
        seen = command_at(commands, th.t[k] - bess.delay_s, p0_kw)
        gap = seen - th.p_act[k]
        dis_cap = 0.0 if soc <= bess.soc_min else bess.p_rated_kw
        chg_cap = 0.0 if soc >= bess.soc_max else bess.p_rated_kw
        target = limit_then_ramp(gap, ramp, dt, chg_cap, dis_cap)
        p_exec = target if bess.tau_s <= 0 else p_exec + (target - p_exec) * min(1.0, dt / bess.tau_s)
        soc = min(max(soc - p_exec * dt / 3600.0 / e, 0.0), 1.0)
        p_b[k] = p_exec
        total[k] = th.p_act[k] + p_exec
    return th, p_b, total

