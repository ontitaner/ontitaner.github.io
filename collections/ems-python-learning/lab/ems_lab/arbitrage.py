"""第 13 章：峰谷套利与计划曲线。

约定：功率 kW（放电为正、充电为负），电量 kWh，电价 元/kWh，SOC 0~1；
日计划默认 96 点、每点 15 分钟（0.25 h），每点表示该时段内的平均功率。
所有电价、效率、退化成本数值都是 [教学示例]，以当地最新政策和项目数据为准。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, tzinfo
from typing import Sequence

SLOTS_PER_DAY = 96
SLOT_H = 0.25
SLOT_S = 900


# ---------------------------------------------------------------- 分时电价
@dataclass(frozen=True)
class TouPeriod:
    start_h: float
    end_h: float
    name: str  # 尖峰 / 峰 / 平 / 谷
    price: float  # 元/kWh


def tou_prices(periods: Sequence[TouPeriod], slots: int = SLOTS_PER_DAY) -> list[float]:
    """把分时电价时段表展开成每个时段一个电价。要求时段不重叠、覆盖全天。"""
    slot_h = 24.0 / slots
    prices: list[float | None] = [None] * slots
    for p in periods:
        if not 0 <= p.start_h < p.end_h <= 24:
            raise ValueError(f"时段 {p} 不合法；跨零点的时段请拆成两段")
        for k in range(slots):
            mid = (k + 0.5) * slot_h
            if p.start_h <= mid < p.end_h:
                if prices[k] is not None:
                    raise ValueError(f"时段重叠：第 {k} 点")
                prices[k] = p.price
    missing = [k for k, v in enumerate(prices) if v is None]
    if missing:
        raise ValueError(f"电价时段没有覆盖全天，缺第 {missing[0]} 点等 {len(missing)} 个点")
    return [float(v) for v in prices]  # type: ignore[arg-type]


# ---------------------------------------------------------------- 单次套利收益
@dataclass(frozen=True)
class CycleProfit:
    discharge_kwh: float  # 放给用户/电网的电量
    charge_kwh: float  # 为此需要从电网买入的电量
    revenue: float  # 放电替代或卖出的收入
    charge_cost: float
    degradation_cost: float
    net: float


def cycle_net_profit(discharge_kwh: float, price_discharge: float, price_charge: float,
                     round_trip_eff: float, degradation_cost_per_kwh: float = 0.0) -> CycleProfit:
    """一次“低价充、高价放”的净收益（参数顺序与第 03 章 economics.arbitrage_cycle 一致）。

    放出 E 度电，需要先买入 E / η 度电（η 为往返效率，充电和放电的损耗都算进去）；
    退化成本按放电量计：每放 1 kWh 消耗掉的电池寿命折算成的钱。
    """
    if not 0 < round_trip_eff <= 1:
        raise ValueError("往返效率必须在 (0, 1]")
    if discharge_kwh < 0:
        raise ValueError("放电量用非负幅值")
    charge_kwh = discharge_kwh / round_trip_eff
    revenue = discharge_kwh * price_discharge
    charge_cost = charge_kwh * price_charge
    deg = discharge_kwh * degradation_cost_per_kwh
    return CycleProfit(discharge_kwh, charge_kwh, revenue, charge_cost, deg, revenue - charge_cost - deg)


def spread_threshold(price_charge: float, round_trip_eff: float, degradation_cost_per_kwh: float = 0.0) -> float:
    """价差门槛：峰谷价差至少要多大，套利才不亏。

    每放 1 kWh 的净收益 = 放电价 − 充电价 / η − 退化成本 ≥ 0
    ⇒ 价差 = 放电价 − 充电价 ≥ 充电价 × (1/η − 1) + 退化成本
    """
    if not 0 < round_trip_eff <= 1:
        raise ValueError("往返效率必须在 (0, 1]")
    return price_charge * (1.0 / round_trip_eff - 1.0) + degradation_cost_per_kwh


# ---------------------------------------------------------------- 计划 SOC 轨迹校验
@dataclass(frozen=True)
class BatterySpec:
    capacity_kwh: float
    p_max_charge_kw: float  # 非负幅值
    p_max_discharge_kw: float  # 非负幅值
    soc_min: float = 0.10
    soc_max: float = 0.90
    eta_charge: float = 0.95  # 单向效率 [教学示例]
    eta_discharge: float = 0.95

    @property
    def round_trip_eff(self) -> float:
        return self.eta_charge * self.eta_discharge


def soc_step(soc: float, p_kw: float, dt_h: float, bat: BatterySpec) -> float:
    """一个时段后的 SOC：放电时电池多出 1/η，充电时只存进 η。"""
    if p_kw >= 0:
        return soc - p_kw * dt_h / bat.eta_discharge / bat.capacity_kwh
    return soc + (-p_kw) * dt_h * bat.eta_charge / bat.capacity_kwh


@dataclass
class PlanCheck:
    soc: list[float]  # 长度 n+1：soc[k] 是第 k 个时段开始时的 SOC
    violations: list[str] = field(default_factory=list)

    @property
    def feasible(self) -> bool:
        return not self.violations


def validate_plan(plan_kw: Sequence[float], bat: BatterySpec, soc0: float, dt_h: float = SLOT_H,
                  soc_end_min: float | None = None, tol: float = 1e-9) -> PlanCheck:
    """功率与电量双重约束下的计划可行性校验。

    逐点检查：功率是否超过充/放能力；按时间累加后的 SOC 是否越过上下限；
    可选：日末 SOC 是否不低于要求（给第二天留电）。
    """
    soc = soc0
    traj = [soc]
    v: list[str] = []
    if not bat.soc_min - tol <= soc0 <= bat.soc_max + tol:
        v.append(f"起始 SOC {soc0:.1%} 不在 [{bat.soc_min:.0%}, {bat.soc_max:.0%}]")
    for k, p in enumerate(plan_kw):
        if p > bat.p_max_discharge_kw + tol:
            v.append(f"第 {k} 点放电 {p:.0f} kW 超过可放 {bat.p_max_discharge_kw:.0f} kW")
        if -p > bat.p_max_charge_kw + tol:
            v.append(f"第 {k} 点充电 {-p:.0f} kW 超过可充 {bat.p_max_charge_kw:.0f} kW")
        soc = soc_step(soc, p, dt_h, bat)
        traj.append(soc)
        if soc > bat.soc_max + tol:
            v.append(f"第 {k} 点结束 SOC {soc:.1%} 超过上限 {bat.soc_max:.0%}")
        if soc < bat.soc_min - tol:
            v.append(f"第 {k} 点结束 SOC {soc:.1%} 低于下限 {bat.soc_min:.0%}")
    if soc_end_min is not None and soc < soc_end_min - tol:
        v.append(f"日末 SOC {soc:.1%} 低于要求 {soc_end_min:.0%}")
    return PlanCheck(traj, v)


# ---------------------------------------------------------------- 排程：简单规则
def rule_based_plan(prices: Sequence[float], bat: BatterySpec, charge_at_or_below: float,
                    discharge_at_or_above: float) -> list[float]:
    """最简单的规则：电价 ≤ 某值就满功率充，≥ 某值就满功率放。不看 SOC，所以必须再校验。"""
    if charge_at_or_below >= discharge_at_or_above:
        raise ValueError("充电电价阈值必须低于放电电价阈值")
    plan = []
    for p in prices:
        if p <= charge_at_or_below:
            plan.append(-bat.p_max_charge_kw)
        elif p >= discharge_at_or_above:
            plan.append(bat.p_max_discharge_kw)
        else:
            plan.append(0.0)
    return plan


# ---------------------------------------------------------------- 排程：按电价排序的贪心
@dataclass
class GreedyPlan:
    plan_kw: list[float]
    pairs: list[tuple[int, int, float]]  # (充电时段, 放电时段, 充电功率 kW)
    expected_profit: float  # 元


def greedy_plan(prices: Sequence[float], bat: BatterySpec, soc0: float,
                degradation_cost_per_kwh: float = 0.0, dt_h: float = SLOT_H) -> GreedyPlan:
    """按价差从大到小“配对”：每一对 = 在便宜的时段充一点、在贵的时段放出同样多的电池电量。

    1. 列出所有 (充电时段 c, 放电时段 d) 组合，算每充 1 kWh 的净收益，只保留 > 0 的；
    2. 按净收益从大到小处理；每一对能安排多少，由三件事决定：
       c 的剩余充电功率、d 的剩余放电功率、c 与 d 之间的 SOC 余量（不越上/下限）；
    3. 一个时段只做一个方向（不会在同一个 15 分钟里又充又放）。
    每一对都让电池电量“存多少取多少”，所以日末 SOC 回到起点，第二天可以重复。
    这是启发式算法，不保证全局最优（最优解见正文的线性规划）。
    """
    n = len(prices)
    eta = bat.round_trip_eff
    charge = [0.0] * n  # 充电功率幅值
    dis = [0.0] * n  # 放电功率幅值
    soc = [soc0] * (n + 1)
    pairs: list[tuple[int, int, float]] = []
    profit = 0.0

    candidates = []
    for c in range(n):
        for d in range(n):
            if c == d:
                continue
            # 每从电网买 1 kWh：放出 η kWh，收入 η·p_d，扣退化成本 η·deg
            value = eta * prices[d] - prices[c] - eta * degradation_cost_per_kwh
            if value > 1e-12:
                candidates.append((-value, c, d))
    candidates.sort()

    for neg_value, c, d in candidates:
        if dis[c] > 0 or charge[d] > 0:
            continue  # 方向冲突
        head_c = bat.p_max_charge_kw - charge[c]
        head_d = bat.p_max_discharge_kw - dis[d]
        x = min(head_c, head_d / eta)  # 充电功率；对应放电功率 x·η
        if c < d:  # 先充后放：c 结束到 d 结束之间 SOC 被抬高
            room = bat.soc_max - max(soc[c + 1:d + 1])
        else:  # 先放后充：d 结束到 c 结束之间 SOC 被压低
            room = min(soc[d + 1:c + 1]) - bat.soc_min
        x = min(x, max(0.0, room) * bat.capacity_kwh / (dt_h * bat.eta_charge))
        if x <= 1e-6:
            continue
        charge[c] += x
        dis[d] += x * eta
        delta = x * dt_h * bat.eta_charge / bat.capacity_kwh
        lo, hi = (c + 1, d + 1) if c < d else (d + 1, c + 1)
        sign = 1.0 if c < d else -1.0
        for k in range(lo, hi):
            soc[k] += sign * delta
        pairs.append((c, d, x))
        profit += -neg_value * x * dt_h

    plan = [dis[k] - charge[k] for k in range(n)]
    return GreedyPlan(plan, pairs, profit)


def plan_energy_cost(plan_kw: Sequence[float], prices: Sequence[float], dt_h: float = SLOT_H) -> float:
    """计划对应的电费变化（元）：放电替代购电为收入，充电为支出。返回净收入。"""
    return sum(p * dt_h * price for p, price in zip(plan_kw, prices))


# ---------------------------------------------------------------- 计划曲线与跟踪
class PlanDateMismatch(ValueError):
    """当前时刻不属于这条计划的日期：常见于跨日切换、时区换算错误。"""


@dataclass(frozen=True)
class PlanCurve:
    """一天的计划曲线：plan_date 是计划所属的“本地日期”，tz 是计划使用的时区。"""

    plan_date: date
    points_kw: tuple[float, ...]
    tz: tzinfo

    def __post_init__(self):
        if len(self.points_kw) != SLOTS_PER_DAY:
            raise ValueError(f"日计划应有 {SLOTS_PER_DAY} 点，实际 {len(self.points_kw)} 点")

    def slot_index(self, ts: datetime) -> int:
        """把一个带时区的时间戳换算成本计划的第几点（0~95）。"""
        if ts.tzinfo is None:
            raise ValueError("时间戳必须带时区；naive datetime 是跨日/时区故障的根源")
        local = ts.astimezone(self.tz)
        if local.date() != self.plan_date:
            raise PlanDateMismatch(f"时刻 {local.isoformat()} 不属于 {self.plan_date} 的计划")
        return (local.hour * 3600 + local.minute * 60 + local.second) // SLOT_S

    def value_at(self, ts: datetime) -> float:
        return self.points_kw[self.slot_index(ts)]


def slot_deviation(planned_kw: float, actual_kwh: float, dt_h: float = SLOT_H) -> tuple[float, float]:
    """一个时段的跟踪偏差：(实际电量 − 计划电量, 相对偏差)。计划为 0 时相对偏差按 0 或 inf 处理。"""
    planned_kwh = planned_kw * dt_h
    dev = actual_kwh - planned_kwh
    if planned_kwh == 0:
        return dev, 0.0 if dev == 0 else float("inf")
    return dev, dev / abs(planned_kwh)

