"""第 21 章：综合项目参考实现——把第 00 章那座工商业光储站的 24 小时，用前面各章的真实模块跑一遍。

日前（第 13 章）：分时电价 → 贪心套利计划（96 点）→ SOC 可行性校验。
实时（每分钟一个周期）：
    计划请求 → 约束区间（第 05/12 章 SOC 分区、设备能力；第 12 章防倒送；第 14 章需量进口上限）
    → 统一投影 project（冲突按优先级放松并上报）→ 光伏限发兜底 → SOC 更新（第 05 章）
    → 并网点功率平衡（第 02 章）→ 决策审计（第 20 章）。
事后：需量（固定窗口，第 14 章）、电费、KPI、约束动作次数。

这是一个 **EMS 级、分钟级** 的教学参考实现：没有 PCS 动态、通信延迟和故障注入（这些在第 19 章 sim.py 中），
目的是验证“各章的模块能正确地组合在一起”。全部参数为 [教学示例]。
约定（附录 B）：P_BESS 放电为正；P_PCC 向电网送电为正；P_import = −P_PCC；功率 kW，电量 kWh，SOC 0～1。
"""
from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field

from .arbitrage import SLOT_H, BatterySpec, TouPeriod, greedy_plan, tou_prices, validate_plan
from .battery import update_soc
from .constraints import (
    SocZoneConfig,
    device_interval,
    export_limit_interval,
    import_limit_interval,
    project,
    soc_interval,
)
from .demand import allowed_import_kw, control_target_kw, fixed_window_demands
from .observability import DecisionAudit, LimitStep
from .power import pcc_injection_kw

VERSION = "mini_ems 0.1"
DT_S = 60.0  # 实时控制周期：1 分钟（教学用；现场按功能取百毫秒～秒级）
STEPS = 1440


# ---------------------------------------------------------------- 场景配置
@dataclass(frozen=True)
class StationConfig:
    capacity_kwh: float = 4000.0
    p_max_kw: float = 1000.0
    soc0: float = 0.15
    eta: float = 0.95  # 单向效率
    degradation_yuan_per_kwh: float = 0.10  # 退化成本（按放电量折算）
    p_aux_kw: float = 20.0
    export_limit_kw: float = 0.0  # 零倒送
    demand_goal_kw: float = 1800.0  # 需量目标
    demand_margin_kw: float = 50.0  # 控制裕度
    soc_zones: SocZoneConfig = field(default_factory=SocZoneConfig)
    tou: tuple[TouPeriod, ...] = (
        TouPeriod(0, 8, "谷", 0.30),
        TouPeriod(8, 12, "峰", 1.10),
        TouPeriod(12, 17, "平", 0.65),
        TouPeriod(17, 21, "峰", 1.10),
        TouPeriod(21, 24, "平", 0.65),
    )
    config_version: str = "day-demo-1"

    @property
    def battery(self) -> BatterySpec:
        z = self.soc_zones
        return BatterySpec(self.capacity_kwh, self.p_max_kw, self.p_max_kw,
                           soc_min=z.stop_discharge_at, soc_max=z.stop_charge_at,
                           eta_charge=self.eta, eta_discharge=self.eta)


def day_profiles(steps: int = STEPS) -> tuple[list[float], list[float]]:
    """与第 00 章配图同一组 [教学示例] 曲线：工厂负荷（凌晨 4:30 夜班大设备启动）与屋顶光伏。"""
    load, pv = [], []
    for k in range(steps):
        h = k * 24.0 / steps
        base = 700 + 800 * (7.5 < h < 19) + 150 * math.sin(h / 24 * 6 * math.pi)
        load.append(base + (1100 if 4.5 <= h < 5.25 else 0.0))
        pv.append(2300 * max(0.0, math.sin((h - 6.5) / 12 * math.pi)) ** 1.5)
    return load, pv


# ---------------------------------------------------------------- 结果
@dataclass
class DayResult:
    cfg: StationConfig
    plan_kw: list[float]  # 96 点日前计划
    plan_expected_profit: float
    load: list[float]
    pv: list[float]
    pv_used: list[float]
    request: list[float] = field(default_factory=list)
    p_bess: list[float] = field(default_factory=list)
    p_pcc: list[float] = field(default_factory=list)
    soc: list[float] = field(default_factory=list)  # 每个周期结束时的 SOC
    audits: list[DecisionAudit] = field(default_factory=list)
    conflicts: list[tuple[int, str, float]] = field(default_factory=list)  # (周期, 约束, 缺口 kW)

    # ---- KPI（口径写在函数里，第 20 章 20.8）
    @property
    def p_import(self) -> list[float]:
        return [-p for p in self.p_pcc]

    def max_demand_kw(self) -> float:
        """固定 15 分钟窗口需量的最大值（进口为正，出口按 0 计）。"""
        return max(fixed_window_demands(self.p_import, DT_S, 900))

    def energy_kwh(self) -> tuple[float, float]:
        """(储能交流侧充电量, 放电量)。"""
        h = DT_S / 3600
        ch = sum(-p for p in self.p_bess if p < 0) * h
        dis = sum(p for p in self.p_bess if p > 0) * h
        return ch, dis

    def grid_energy_cost(self) -> float:
        """并网点购电电费（元），不含需量电费；倒送电量按 0 结算（本项目不允许倒送）。"""
        prices = tou_prices(self.cfg.tou, STEPS)
        return sum(max(0.0, imp) * DT_S / 3600 * pr for imp, pr in zip(self.p_import, prices))

    def max_backfeed_kw(self) -> float:
        return max(0.0, max(self.p_pcc))

    def pv_curtailed_kwh(self) -> float:
        return sum(a - b for a, b in zip(self.pv, self.pv_used)) * DT_S / 3600

    def binding_counts(self) -> Counter:
        return Counter(name for a in self.audits for name in a.binding())

    def power_balance_residual_kw(self) -> float:
        aux = self.cfg.p_aux_kw
        return max(abs(pcc - pcc_injection_kw(b, ld, aux, 0.0, pv))
                   for pcc, b, ld, pv in zip(self.p_pcc, self.p_bess, self.load, self.pv_used))


# ---------------------------------------------------------------- 主流程
def run_day(cfg: StationConfig = StationConfig(), use_constraints: bool = True) -> DayResult:
    """use_constraints=False 是对照组：只执行日前计划（仍受设备额定和 SOC 物理边界），不做实时约束。"""
    load, pv = day_profiles()
    bat = cfg.battery

    # 1) 日前：电价 → 计划 → 校验（第 13 章）
    prices96 = tou_prices(cfg.tou)
    gp = greedy_plan(prices96, bat, cfg.soc0, cfg.degradation_yuan_per_kwh)
    check = validate_plan(gp.plan_kw, bat, cfg.soc0, SLOT_H)
    if not check.feasible:
        raise ValueError(f"日前计划不可执行：{check.violations[:3]}")

    res = DayResult(cfg, gp.plan_kw, gp.expected_profit, load, pv, list(pv))
    target_kw = control_target_kw(cfg.demand_goal_kw, cfg.demand_margin_kw)
    soc = cfg.soc0
    e_window_kwh = 0.0  # 本需量周期已累计的进口电量（与电表的 15 分钟窗口对齐，第 14 章）

    for k in range(STEPS):
        t = k * DT_S
        t_in_window = t % 900
        if t_in_window == 0:
            e_window_kwh = 0.0
        request = gp.plan_kw[int(k * DT_S // (SLOT_H * 3600))]

        # 2) 约束区间：设备能力 → SOC 分区 → 防倒送 → 需量进口上限（第 12、14 章）
        intervals = [device_interval(cfg.p_max_kw, cfg.p_max_kw), soc_interval(soc, cfg.p_max_kw, cfg.soc_zones)]
        if use_constraints:
            # 本周期剩余时间内允许的平均进口功率：已经用掉的“电量预算”越多，允许值越小
            allowed = allowed_import_kw(e_window_kwh, 900 - t_in_window, target_kw)
            intervals += [
                export_limit_interval(load[k], pv[k], cfg.export_limit_kw, cfg.p_aux_kw),
                import_limit_interval(load[k], pv[k], allowed, cfg.p_aux_kw, name="需量控制", priority=1),
            ]
        r = project(request, intervals)
        p = r.final_kw
        for c in r.conflicts:
            res.conflicts.append((k, c.name, c.shortfall_kw))

        # 3) 光伏限发兜底：储能吸收不了的余电，由光伏逆变器限发（仍然不倒送）
        pv_used = pv[k]
        if use_constraints:
            export = pcc_injection_kw(p, load[k], cfg.p_aux_kw, 0.0, pv[k])
            if export > cfg.export_limit_kw:
                pv_used = pv[k] - (export - cfg.export_limit_kw)

        # 4) 物理更新：SOC（第 05 章）、并网点（第 02 章）、需量跟踪（第 14 章）
        u = update_soc(soc, p, DT_S, cfg.capacity_kwh, cfg.eta, cfg.eta)
        soc = u.soc
        p_pcc = pcc_injection_kw(p, load[k], cfg.p_aux_kw, 0.0, pv_used)
        e_window_kwh += max(0.0, -p_pcc) * DT_S / 3600

        # 5) 决策审计（第 20 章）：按“生效顺序”记录每个约束的前后值
        steps, x = [], request
        for iv in sorted(intervals, key=lambda i: (i.layer, i.priority)):
            lo, hi = round(iv.lower_kw, 1), round(iv.upper_kw, 1)  # 审计记录保留 0.1 kW 即可
            after = min(max(x, lo), hi) if lo <= hi else x
            steps.append(LimitStep(iv.name, lo, hi, x, after))
            x = after
        if abs(x - p) > 0.05:  # 冲突放松后结果与逐个限幅不同：以投影结果为准并记下原因
            steps.append(LimitStep("冲突放松", p, p, x, p))
        res.audits.append(DecisionAudit(
            cycle_id=k, seq=k + 1, t_mono_s=t, t_wall=f"{int(t // 3600):02d}:{int(t % 3600 // 60):02d}",
            mode="计划跟踪", requests=[("日前计划", request)], requested_kw=request, steps=steps, final_kw=p,
            soc=soc, avail_charge_kw=cfg.p_max_kw, avail_discharge_kw=cfg.p_max_kw,
            data_quality={"pcc_meter": "GOOD", "bms": "GOOD"}, config_version=cfg.config_version,
            software_version=VERSION, ack="接受", actual_kw=p,
        ))

        res.request.append(request)
        res.p_bess.append(p)
        res.pv_used[k] = pv_used
        res.p_pcc.append(p_pcc)
        res.soc.append(soc)
    return res

@dataclass(frozen=True)
class Baseline:
    """对照组：没有储能。光伏富余时只能限发（零倒送）。"""
    grid_energy_cost: float
    max_demand_kw: float
    pv_curtailed_kwh: float


def baseline_no_storage(cfg: StationConfig = StationConfig()) -> Baseline:
    load, pv = day_profiles()
    prices = tou_prices(cfg.tou, STEPS)
    imports, curtailed = [], 0.0
    for ld, g in zip(load, pv):
        imp = ld + cfg.p_aux_kw - g
        if imp < 0:  # 富余光伏限发
            curtailed += -imp * DT_S / 3600
            imp = 0.0
        imports.append(imp)
    cost = sum(i * DT_S / 3600 * p for i, p in zip(imports, prices))
    return Baseline(cost, max(fixed_window_demands(imports, DT_S, 900)), curtailed)

