"""第 14 章：需量管理。

约定：
- 需量只用进口功率 P_import（从电网取电为正，P_import = −P_PCC）；
- 需量 = 一个需量周期（常见 15 分钟）内的平均进口功率 = 周期内进口电量 / 周期时长；
- 倒送的电量不抵扣进口需量（本课程默认，以电能表设置和供电合同为准）；
- 功率 kW，电量 kWh，时间 s。基本电费单价一律为 [教学示例]，以当地政策和供电合同为准。
"""
from __future__ import annotations

import math
from typing import Sequence

KWS_PER_KWH = 3600.0


def demand_power_kw(p_import_kw: float) -> float:
    """计入需量的功率：只累计进口，倒送时记 0。"""
    return max(0.0, p_import_kw)


def _check_grid(dt_s: float, window_s: float, step_s: float | None = None) -> int:
    if dt_s <= 0 or window_s <= 0:
        raise ValueError("采样间隔和需量周期必须为正")
    n = window_s / dt_s
    if abs(n - round(n)) > 1e-9:
        raise ValueError("需量周期必须是采样间隔的整数倍")
    if step_s is not None:
        m = step_s / dt_s
        if step_s <= 0 or abs(m - round(m)) > 1e-9:
            raise ValueError("滑差步长必须是采样间隔的正整数倍")
    return int(round(n))


def fixed_window_demands(p_import_kw: Sequence[float], dt_s: float, window_s: float = 900,
                         offset_s: float = 0) -> list[float]:
    """固定窗口需量：从 offset 开始，每 window_s 切一段，每段一个平均值（只算完整窗口）。

    p_import_kw[i] 表示第 i 个采样间隔内的平均进口功率（例如电表 1 分钟电量换算的功率）。
    offset_s 用来模拟“EMS 的窗口起点和电表不一致”。
    """
    n = _check_grid(dt_s, window_s)
    off = _check_grid(dt_s, offset_s) if offset_s else 0
    vals = [demand_power_kw(p) for p in p_import_kw]
    out = []
    for start in range(off, len(vals) - n + 1, n):
        out.append(sum(vals[start:start + n]) / n)
    return out


def sliding_window_demands(p_import_kw: Sequence[float], dt_s: float, window_s: float = 900,
                           step_s: float = 60) -> list[float]:
    """滑差需量：窗口长度不变，每隔 step_s 向后滑动一次，每次算一个平均值。

    例如 15 分钟周期、1 分钟滑差：每分钟都算一次“最近 15 分钟平均”。
    同一段数据，滑差方式的最大值 ≥ 固定窗口方式的最大值。
    """
    n = _check_grid(dt_s, window_s, step_s)
    step = int(round(step_s / dt_s))
    vals = [demand_power_kw(p) for p in p_import_kw]
    return [sum(vals[s:s + n]) / n for s in range(0, len(vals) - n + 1, step)]


def predict_demand_kw(e_elapsed_kwh: float, p_assumed_kw: float, t_remain_s: float,
                      window_s: float = 900) -> float:
    """需量预测：D_predict = (已累计电量 + 假设功率 × 剩余时间) / 周期。"""
    if not 0 <= t_remain_s <= window_s:
        raise ValueError("剩余时间必须在 0 到周期长度之间")
    e_total = e_elapsed_kwh + demand_power_kw(p_assumed_kw) * t_remain_s / KWS_PER_KWH
    return e_total / (window_s / KWS_PER_KWH)


def allowed_import_kw(e_elapsed_kwh: float, t_remain_s: float, target_kw: float,
                      window_s: float = 900) -> float:
    """本周期剩余时间内，平均进口功率最多还能是多少，才能让周期需量 ≤ 目标。

    允许电量 = 目标 × 周期 − 已累计电量；除以剩余时间就是允许的平均进口功率。
    结果可能为负：已累计电量已经超过预算，本周期无论如何都会超目标。
    """
    if t_remain_s <= 0:
        raise ValueError("周期已结束，没有剩余时间可以调节")
    budget_kwh = target_kw * window_s / KWS_PER_KWH - e_elapsed_kwh
    return budget_kwh / (t_remain_s / KWS_PER_KWH)


def required_extra_discharge_kw(e_elapsed_kwh: float, p_import_now_kw: float, t_remain_s: float,
                                target_kw: float, window_s: float = 900) -> float:
    """为了不超过目标，储能需要在剩余时间内额外放电多少（假设负荷保持当前水平）。"""
    allowed = allowed_import_kw(e_elapsed_kwh, t_remain_s, target_kw, window_s)
    return max(0.0, p_import_now_kw - allowed)


def control_target_kw(demand_goal_kw: float, margin_kw: float) -> float:
    """控制目标 = 需量目标 − 裕度。裕度用来吸收计量误差、窗口不对齐、通信和执行延迟。"""
    if margin_kw < 0 or margin_kw >= demand_goal_kw:
        raise ValueError("裕度必须非负且小于目标")
    return demand_goal_kw - margin_kw


def basic_charge_by_demand(max_demand_kw: float, price_per_kw_month: float) -> float:
    """按最大需量计收的月基本电费 = 月最大需量 × 单价 [教学示例单价]。"""
    return max(0.0, max_demand_kw) * price_per_kw_month


def basic_charge_by_capacity(capacity_kva: float, price_per_kva_month: float) -> float:
    """按变压器容量计收的月基本电费 = 容量 × 单价 [教学示例单价]。与实际用了多少无关。"""
    return capacity_kva * price_per_kva_month


def monthly_max_demand(window_demands_kw: Sequence[float]) -> float:
    """月最大需量：整月所有需量周期里的最大值。一次峰值就决定整月。"""
    return max(window_demands_kw, default=0.0)


class DemandWindowTracker:
    """EMS 内部的需量周期跟踪器（固定窗口）。

    每个控制周期调用 update(t_s, p_import_kw)：按“上一个采样值保持到这一刻”累加电量；
    跨过窗口边界时自动开始新周期。t_s 应来自与电表对齐的时钟（第 14 章现场故障）。
    """

    def __init__(self, window_s: float = 900, target_kw: float = math.inf, align_offset_s: float = 0.0):
        if window_s <= 0:
            raise ValueError("需量周期必须为正")
        self.window_s = window_s
        self.target_kw = target_kw
        self.align_offset_s = align_offset_s
        self.window_index: int | None = None
        self.energy_kwh = 0.0
        self._last_t: float | None = None
        self._last_p = 0.0
        self.completed: list[float] = []  # 已结束周期的需量

    def _index(self, t_s: float) -> int:
        return math.floor((t_s - self.align_offset_s) / self.window_s)

    def window_start_s(self) -> float:
        if self.window_index is None:
            raise RuntimeError("尚未收到数据")
        return self.window_index * self.window_s + self.align_offset_s

    def update(self, t_s: float, p_import_kw: float) -> None:
        if self._last_t is not None and t_s <= self._last_t:
            raise ValueError("时间戳未递增")
        idx = self._index(t_s)
        if self.window_index is None:
            self.window_index = idx
        elif self._last_t is not None:
            t = self._last_t
            while idx > self.window_index:  # 把上一个采样值累加到窗口边界，然后结算
                boundary = (self.window_index + 1) * self.window_s + self.align_offset_s
                self.energy_kwh += demand_power_kw(self._last_p) * (boundary - t) / KWS_PER_KWH
                self.completed.append(self.energy_kwh / (self.window_s / KWS_PER_KWH))
                self.energy_kwh = 0.0
                self.window_index += 1
                t = boundary
            self.energy_kwh += demand_power_kw(self._last_p) * (t_s - t) / KWS_PER_KWH
        self._last_t = t_s
        self._last_p = p_import_kw

    @property
    def elapsed_s(self) -> float:
        return 0.0 if self._last_t is None else self._last_t - self.window_start_s()

    @property
    def remaining_s(self) -> float:
        return self.window_s - self.elapsed_s

    def predict(self, p_assumed_kw: float | None = None) -> float:
        """默认假设“当前功率保持到周期结束”。"""
        p = self._last_p if p_assumed_kw is None else p_assumed_kw
        return predict_demand_kw(self.energy_kwh, p, self.remaining_s, self.window_s)

    def allowed_import_kw(self) -> float:
        return allowed_import_kw(self.energy_kwh, self.remaining_s, self.target_kw, self.window_s)

