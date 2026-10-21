"""第 18 章：多 PCS / 多簇功率分配——按能力比例、SOC 均衡、离线重分配、余量迭代再分配。

约定：有功 kW，放电为正、充电为负；SOC 0~1；可充/可放能力为非负幅值。
分配器只负责“把已经仲裁、投影过的总功率分下去”，分不完的部分要作为未满足量上报。
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Mapping, Sequence


@dataclass
class Unit:
    name: str
    available_charge_kw: float
    available_discharge_kw: float
    soc: float = 0.5
    energy_kwh: float = 1000.0
    online: bool = True  # 通信中断、故障、检修 → False

    def __post_init__(self):
        if self.available_charge_kw < 0 or self.available_discharge_kw < 0:
            raise ValueError(f"{self.name}：可充/可放能力必须是非负幅值")

    def capacity(self, discharging: bool) -> float:
        """本方向的可用能力；离线设备能力为 0（不能指望它执行指令）。"""
        if not self.online:
            return 0.0
        return self.available_discharge_kw if discharging else self.available_charge_kw


@dataclass
class AllocationResult:
    setpoints: dict[str, float]
    requested_kw: float
    allocated_kw: float
    unserved_kw: float  # requested − allocated（带方向）
    iterations: int
    notes: list[str] = field(default_factory=list)


def water_fill(total_kw: float, caps: Mapping[str, float], weights: Mapping[str, float]) -> tuple[dict[str, float], int]:
    """按权重分配非负总量 total_kw，单机不超过 cap；超出部分迭代再分配给还有余量的设备。

    返回 (各设备分配量, 迭代次数)。分不完的量由调用方用 total − sum 得到。
    """
    if total_kw < 0:
        raise ValueError("water_fill 只处理非负幅值，方向由调用方处理")
    alloc = {n: 0.0 for n in caps}
    active = [n for n in caps if caps[n] > 0 and weights.get(n, 0.0) > 0]
    remaining, it = total_kw, 0
    while remaining > 1e-9 and active:
        it += 1
        wsum = sum(weights[n] for n in active)
        share = {n: remaining * weights[n] / wsum for n in active}
        saturated = [n for n in active if alloc[n] + share[n] >= caps[n] - 1e-9]
        if not saturated:
            for n in active:
                alloc[n] += share[n]
            remaining = 0.0
            break
        for n in saturated:  # 顶到上限的设备先固定，余量留给下一轮
            remaining -= caps[n] - alloc[n]
            alloc[n] = caps[n]
        active = [n for n in active if n not in saturated]
    return alloc, it


def _allocate(p_total_kw: float, units: Sequence[Unit], weight_fn, label: str) -> AllocationResult:
    discharging = p_total_kw >= 0
    sign = 1.0 if discharging else -1.0
    caps = {u.name: u.capacity(discharging) for u in units}
    weights = {u.name: weight_fn(u, discharging) if caps[u.name] > 0 else 0.0 for u in units}
    notes = [f"{u.name} 离线，能力置 0" for u in units if not u.online]
    if sum(weights.values()) <= 0 and sum(caps.values()) > 0:
        weights = dict(caps)  # 权重全为 0（例如 SOC 全在边界）时退回按能力分配
        notes.append(f"{label} 权重全为 0，退回按能力比例")
    alloc, it = water_fill(abs(p_total_kw), caps, weights)
    setpoints = {n: sign * v for n, v in alloc.items()}
    allocated = sum(setpoints.values())
    unserved = p_total_kw - allocated
    if abs(unserved) > 1e-6:
        notes.append(f"可用能力不足，未满足 {unserved:.1f} kW")
    return AllocationResult(setpoints, p_total_kw, allocated, unserved, it, notes)


def allocate_by_capability(p_total_kw: float, units: Sequence[Unit]) -> AllocationResult:
    """按本方向可用能力比例分配：能力大的多分，所有设备同时到达上限。"""
    return _allocate(p_total_kw, units, lambda u, d: u.capacity(d), "按能力")


def allocate_soc_balance(p_total_kw: float, units: Sequence[Unit], soc_min: float = 0.05,
                         soc_max: float = 0.95, gamma: float = 1.0) -> AllocationResult:
    """SOC 均衡：按“本方向还能放/充的电量”加权。

    放电权重 = [(SOC − SOC_min) × 容量]^γ，SOC 高的多放；
    充电权重 = [(SOC_max − SOC) × 容量]^γ，SOC 低的多充。
    γ = 1：各簇剩余电量按同一比例减少，**同时**到达下限（SOC 差距按比例缩小）；
    γ > 1：SOC 高的簇分得更多，SOC 差距收敛更快。γ 为 [教学示例] 参数。
    单机仍受可用功率限制，顶满后余量迭代再分配。
    """
    if gamma <= 0:
        raise ValueError("gamma 必须为正")

    def w(u: Unit, discharging: bool) -> float:
        room = (u.soc - soc_min) if discharging else (soc_max - u.soc)
        return (max(0.0, room) * u.energy_kwh) ** gamma

    return _allocate(p_total_kw, units, w, "SOC 均衡")


def round_setpoints(result: AllocationResult, units: Sequence[Unit], resolution_kw: float = 1.0) -> AllocationResult:
    """按设备设定分辨率取整，再把取整误差补给余量最大的设备，保证总和不变（在能力允许内）。"""
    if resolution_kw <= 0:
        raise ValueError("分辨率必须为正")
    discharging = result.allocated_kw >= 0
    caps = {u.name: u.capacity(discharging) for u in units}
    sign = 1.0 if discharging else -1.0
    sp = {n: round(v / resolution_kw) * resolution_kw for n, v in result.setpoints.items()}
    residual = round((result.allocated_kw - sum(sp.values())) / resolution_kw)
    step = math.copysign(resolution_kw, residual) if residual else 0.0
    for _ in range(abs(int(residual))):
        # 补差：放电方向补正数时选余量最大的，扣减时选分得最多的
        if step * sign > 0:
            n = max(sp, key=lambda k: caps[k] - abs(sp[k]))
            if caps[n] - abs(sp[n]) < resolution_kw:
                break
        else:
            n = max(sp, key=lambda k: abs(sp[k]))
        sp[n] += step
    total = sum(sp.values())
    notes = result.notes + ([f"取整分辨率 {resolution_kw} kW"] if resolution_kw != 1.0 else [])
    return AllocationResult(sp, result.requested_kw, total, result.requested_kw - total, result.iterations, notes)


def check_allocation(result: AllocationResult, units: Sequence[Unit], tol_kw: float = 1e-6) -> list[str]:
    """分配后校验：总和一致、单机不越限、离线设备为 0、方向一致。返回问题清单（空表示通过）。"""
    issues: list[str] = []
    if abs(sum(result.setpoints.values()) - result.allocated_kw) > tol_kw:
        issues.append("各机之和 ≠ 已分配总量")
    if abs(result.requested_kw - result.allocated_kw - result.unserved_kw) > tol_kw:
        issues.append("请求 ≠ 已分配 + 未满足")
    for u in units:
        p = result.setpoints.get(u.name, 0.0)
        if not u.online and p != 0:
            issues.append(f"{u.name} 离线但分配了 {p:.1f} kW")
        if p > u.available_discharge_kw + tol_kw or -p > u.available_charge_kw + tol_kw:
            issues.append(f"{u.name} 越限：{p:.1f} kW")
        if p * result.requested_kw < -tol_kw:
            issues.append(f"{u.name} 方向与总指令相反")
    return issues


def units_to_run(p_total_kw: float, unit_rated_kw: float, n_available: int, min_load_ratio: float = 0.2,
                 prefer: str = "min") -> int:
    """【了解】启停台数。

    - prefer="min"：开够扛住总功率的最少台数，每台负载率高（PCS 轻载效率低）；
    - prefer="spread"：在每台不低于最小运行功率的前提下尽量多开（利于 SOC 均衡和冗余）。
    总功率低于单台最小运行功率时仍返回 1，由调用方决定是否转待机。
    min_load_ratio 为 [教学示例]，以设备说明书为准。
    """
    if unit_rated_kw <= 0 or n_available < 0 or not 0 <= min_load_ratio < 1:
        raise ValueError("参数非法")
    if prefer not in ("min", "spread"):
        raise ValueError("prefer 只能是 'min' 或 'spread'")
    p = abs(p_total_kw)
    if p == 0 or n_available == 0:
        return 0
    n_need = math.ceil(p / unit_rated_kw - 1e-9)
    if n_need >= n_available:
        return n_available  # 全开也可能不够，差额由分配器作为未满足量上报
    if prefer == "min":
        return n_need
    n_max = n_available if min_load_ratio == 0 else math.floor(p / (min_load_ratio * unit_rated_kw) + 1e-9)
    return max(n_need, min(n_available, n_max))


def simulate_soc(units: Sequence[Unit], p_total_kw: float, duration_s: float, dt_s: float, method: str = "soc",
                 soc_min: float = 0.05, soc_max: float = 0.95, gamma: float = 1.0):
    """用分配器反复分配恒定总功率，记录各簇 SOC 轨迹（用于第 18 章配图）。

    SOC 到限时该簇本方向能力归零（真实系统由 BMS 给出）。返回 (时间列表, {簇名: SOC 列表}, 未满足列表)。
    """
    import copy

    us = [copy.copy(u) for u in units]
    rated = {u.name: (u.available_charge_kw, u.available_discharge_kw) for u in us}
    times, socs, unserved = [], {u.name: [] for u in us}, []
    t = 0.0
    while t <= duration_s + 1e-9:
        for u in us:
            chg, dis = rated[u.name]
            u.available_discharge_kw = 0.0 if u.soc <= soc_min else dis
            u.available_charge_kw = 0.0 if u.soc >= soc_max else chg
        if method == "soc":
            r = allocate_soc_balance(p_total_kw, us, soc_min, soc_max, gamma)
        elif method == "capability":
            r = allocate_by_capability(p_total_kw, us)
        else:
            raise ValueError(f"未知方法：{method}")
        times.append(t)
        unserved.append(r.unserved_kw)
        for u in us:
            socs[u.name].append(u.soc)
            u.soc -= r.setpoints[u.name] * dt_s / 3600.0 / u.energy_kwh
            u.soc = min(max(u.soc, 0.0), 1.0)
        t += dt_s
    return times, socs, unserved

