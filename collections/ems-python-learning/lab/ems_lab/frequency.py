"""第 15 章：频率响应——一次调频（下垂）、RoCoF、虚拟惯量。

约定：频率 Hz，功率 kW，放电为正；
频率低于额定值 → 输出正功率（放电）；频率高于额定值 → 输出负功率（充电）。
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from .control import clamp, deadband_cut, deadband_shift

F_NOMINAL_HZ = 50.0


def droop_gain_kw_per_hz(p_rated_kw: float, droop_ratio: float, f_nominal_hz: float = F_NOMINAL_HZ) -> float:
    """由调差率 δ 换算下垂系数 K = Pn / (δ · fn)，单位 kW/Hz。

    δ = 2% 的含义：频率变化额定值的 2%（1 Hz），出力变化 100% 额定功率。
    """
    if p_rated_kw <= 0 or droop_ratio <= 0:
        raise ValueError("额定功率和调差率必须为正")
    return p_rated_kw / (droop_ratio * f_nominal_hz)


@dataclass
class PrimaryFrequencyConfig:
    p_rated_kw: float
    droop_ratio: float = 0.02  # 调差率 δ [教学示例]
    deadband_hz: float = 0.03  # 死区 ±0.03 Hz [教学示例]
    limit_ratio: float = 0.10  # 一次调频出力限幅，占额定功率比例 [教学示例]
    deadband_mode: str = "shift"  # "shift" 连续型（从死区边界起算）/ "cut" 截断型
    f_nominal_hz: float = F_NOMINAL_HZ


def primary_frequency_power(f_hz: float, cfg: PrimaryFrequencyConfig) -> float:
    """一次调频功率增量 ΔP（叠加在计划/AGC 基点之上），单位 kW。"""
    delta_f = f_hz - cfg.f_nominal_hz
    if cfg.deadband_mode == "shift":
        effective = deadband_shift(delta_f, cfg.deadband_hz)
    elif cfg.deadband_mode == "cut":
        effective = deadband_cut(delta_f, cfg.deadband_hz)
    else:
        raise ValueError(f"未知死区类型：{cfg.deadband_mode}")
    k = droop_gain_kw_per_hz(cfg.p_rated_kw, cfg.droop_ratio, cfg.f_nominal_hz)
    delta_p = -k * effective  # 负号：频率低（Δf<0）→ 正功率 → 放电
    limit = cfg.limit_ratio * cfg.p_rated_kw
    return clamp(delta_p, -limit, limit)


def swing_rocof_hz_per_s(delta_p_pu: float, inertia_h_s: float, f_nominal_hz: float = F_NOMINAL_HZ) -> float:
    """摇摆方程（忽略负荷阻尼，扰动初瞬）：df/dt = fn · ΔP / (2H)。

    delta_p_pu：功率缺口占系统容量的比例，发电不足为负。
    inertia_h_s：系统惯性时间常数 H（秒）。
    """
    if inertia_h_s <= 0:
        raise ValueError("惯性时间常数必须为正")
    return f_nominal_hz * delta_p_pu / (2.0 * inertia_h_s)


def virtual_inertia_power(
    rocof_hz_per_s: float, h_virtual_s: float, s_rated_kw: float, f_nominal_hz: float = F_NOMINAL_HZ
) -> float:
    """虚拟惯量功率 ΔP = −2·H_v·Sn / fn · df/dt。频率下跌越快，放电越多。"""
    return -2.0 * h_virtual_s * s_rated_kw / f_nominal_hz * rocof_hz_per_s


class RocofEstimator:
    """用滑动时间窗口内的最小二乘直线斜率估计 df/dt（Hz/s）。

    比“相邻两点相减”抗噪声，代价是约半个窗口的延迟。
    """

    def __init__(self, window_s: float):
        if window_s <= 0:
            raise ValueError("窗口必须为正")
        self.window_s = window_s
        self.samples: deque[tuple[float, float]] = deque()

    def update(self, t_s: float, f_hz: float) -> float | None:
        if self.samples and t_s <= self.samples[-1][0]:
            raise ValueError("时间戳未递增")
        self.samples.append((t_s, f_hz))
        while t_s - self.samples[0][0] > self.window_s:
            self.samples.popleft()
        n = len(self.samples)
        if n < 3:
            return None  # 样本不足，不给结论
        mean_t = sum(t for t, _ in self.samples) / n
        mean_f = sum(f for _, f in self.samples) / n
        num = sum((t - mean_t) * (f - mean_f) for t, f in self.samples)
        den = sum((t - mean_t) ** 2 for t, _ in self.samples)
        return num / den

