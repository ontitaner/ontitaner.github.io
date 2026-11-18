"""第 11 章：EMS 控制基础函数。

约定：功率单位 kW，放电为正、充电为负；时间单位 s。
每个函数都只做一件事，便于单独测试，再在控制流水线里组合使用。
"""
from __future__ import annotations

import math
from bisect import bisect_right
from typing import Sequence


# ---------------------------------------------------------------- 限幅
def clamp(value: float, lower: float, upper: float) -> float:
    """把 value 压回 [lower, upper] 区间。

    - 含 NaN 直接报错：Python 的 max/min 遇到 NaN 结果取决于参数顺序，不可靠；
    - lower > upper 表示“可行域为空”（约束互相冲突），必须上报，不能随便取一个边界。
    """
    if math.isnan(value) or math.isnan(lower) or math.isnan(upper):
        raise ValueError("clamp 输入含 NaN，应在数据校验层拦截")
    if lower > upper:
        raise ValueError(f"可行域为空：lower={lower} > upper={upper}")
    return max(lower, min(upper, value))


def clamp_power(p_request_kw: float, available_charge_kw: float, available_discharge_kw: float) -> float:
    """按方向限幅：允许区间是 [-可充功率, +可放功率]，两边通常不对称。

    可充/可放功率一律用非负幅值表示（BMS/PCS 点表的常见做法）。
    """
    if available_charge_kw < 0 or available_discharge_kw < 0:
        raise ValueError("可充/可放能力必须是非负幅值")
    return clamp(p_request_kw, -available_charge_kw, available_discharge_kw)


# ---------------------------------------------------------------- 死区
def deadband_cut(x: float, width: float) -> float:
    """截断型死区：|x| ≤ width 输出 0，超出后输出原值。边界处有跳变。"""
    if width < 0:
        raise ValueError("死区宽度必须非负")
    return 0.0 if abs(x) <= width else x


def deadband_shift(x: float, width: float) -> float:
    """连续型死区：|x| ≤ width 输出 0，超出后减去死区宽度。边界处连续、无跳变。"""
    if width < 0:
        raise ValueError("死区宽度必须非负")
    if abs(x) <= width:
        return 0.0
    return x - width if x > 0 else x + width


# ---------------------------------------------------------------- 滞回
class Hysteresis:
    """滞回开关：x 低于 on_below 时打开，高于 off_above 时关闭，中间区域保持原状态。

    典型用途：SOC 低于 15% 开始自充，高于 25% 才停止。
    """

    def __init__(self, on_below: float, off_above: float, initial: bool = False):
        if on_below >= off_above:
            raise ValueError("打开阈值必须小于关闭阈值，否则没有滞回区")
        self.on_below = on_below
        self.off_above = off_above
        self.active = initial

    def update(self, x: float) -> bool:
        if not self.active and x < self.on_below:
            self.active = True
        elif self.active and x > self.off_above:
            self.active = False
        return self.active


# ---------------------------------------------------------------- 变化率限制
class RateLimiter:
    """功率变化率限制（Ramp），单位 kW/s。

    up_rate 限制输出“代数值增大”的速度，down_rate 限制“代数值减小”的速度。
    输出是有状态的：它记得上一次输出了多少。
    """

    def __init__(self, up_rate: float, down_rate: float, initial: float = 0.0):
        if up_rate < 0 or down_rate < 0:
            raise ValueError("变化率必须非负")
        self.up_rate = up_rate
        self.down_rate = down_rate
        self.output = initial

    def update(self, target: float, dt: float) -> float:
        if dt < 0:
            raise ValueError("dt 必须非负")
        delta = clamp(target - self.output, -self.down_rate * dt, self.up_rate * dt)
        self.output += delta
        return self.output

    def reset(self, value: float) -> None:
        """把内部状态同步到实际下发值（例如被后级安全限幅截断之后）。"""
        self.output = value


def limit_then_ramp(
    p_request_kw: float,
    ramp: RateLimiter,
    dt: float,
    available_charge_kw: float,
    available_discharge_kw: float,
) -> float:
    """推荐组合：限幅 → Ramp → 再限幅兜底，并把兜底结果同步回 Ramp 状态。

    为什么要“再限幅”：BMS 突然降额时，可行域瞬间缩小，
    如果只靠 Ramp 慢慢降，会有若干个周期超出安全能力。
    """
    target = clamp_power(p_request_kw, available_charge_kw, available_discharge_kw)
    ramped = ramp.update(target, dt)
    final = clamp_power(ramped, available_charge_kw, available_discharge_kw)
    if final != ramped:
        ramp.reset(final)
    return final


# ---------------------------------------------------------------- 滤波
class LowPassFilter:
    """一阶低通滤波：y ← y + α·(x − y)，其中 α = dt / (τ + dt)。

    τ（时间常数，秒）的物理含义：输入阶跃后，输出走完 63.2% 所需的时间。
    τ 越大越平滑，但延迟越大。
    """

    def __init__(self, tau_s: float):
        if tau_s < 0:
            raise ValueError("时间常数必须非负")
        self.tau_s = tau_s
        self.output: float | None = None

    def update(self, x: float, dt: float) -> float:
        if self.output is None:  # 第一个样本直接作为初值，避免从 0 慢慢爬升
            self.output = x
            return x
        alpha = 1.0 if self.tau_s == 0 else dt / (self.tau_s + dt)
        self.output += alpha * (x - self.output)
        return self.output


# ---------------------------------------------------------------- 查表插值
def interp_table(x: float, xs: Sequence[float], ys: Sequence[float]) -> float:
    """分段线性插值，超出表格范围时取端点值（不外推）。

    典型用途：厂商给出“温度 → 允许功率比例”的降额表，EMS 按当前温度查表。
    """
    if len(xs) != len(ys) or len(xs) < 2:
        raise ValueError("表格至少需要 2 个点，且 xs/ys 等长")
    if any(b <= a for a, b in zip(xs, xs[1:])):
        raise ValueError("xs 必须严格递增")
    if x <= xs[0]:
        return ys[0]
    if x >= xs[-1]:
        return ys[-1]
    i = bisect_right(xs, x)
    x0, x1, y0, y1 = xs[i - 1], xs[i], ys[i - 1], ys[i]
    return y0 + (y1 - y0) * (x - x0) / (x1 - x0)


# ---------------------------------------------------------------- PI 控制
class PIController:
    """带输出限幅和抗积分饱和（条件积分）的离散 PI 控制器。

    u = 前馈 + Kp·e + ∫Ki·e·dt，然后限幅到 [out_min, out_max]。
    抗饱和规则：输出已经顶到上/下限、而误差还在继续把它往外推时，冻结积分。
    """

    def __init__(self, kp: float, ki: float, out_min: float, out_max: float, anti_windup: bool = True):
        if out_min > out_max:
            raise ValueError("out_min 不能大于 out_max")
        self.kp = kp
        self.ki = ki
        self.out_min = out_min
        self.out_max = out_max
        self.anti_windup = anti_windup
        self.integral = 0.0
        self.saturated = False

    def update(self, error: float, dt: float, feedforward: float = 0.0) -> float:
        i_candidate = self.integral + self.ki * error * dt
        u_unsat = feedforward + self.kp * error + i_candidate
        u = clamp(u_unsat, self.out_min, self.out_max)
        pushing_out = (u_unsat > self.out_max and error > 0) or (u_unsat < self.out_min and error < 0)
        if not (self.anti_windup and pushing_out):
            self.integral = i_candidate
        self.saturated = u != u_unsat
        return u

    def reset(self, integral: float = 0.0) -> None:
        """模式切换或控制器重启时调用，避免带着旧积分进入新模式。"""
        self.integral = integral
        self.saturated = False

