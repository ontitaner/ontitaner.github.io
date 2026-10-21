"""第 01、03 章：电网经济性直觉与储能收益计算。

第 01 章部分：输电损耗、净负荷（鸭子曲线）、负荷曲线统计、爬坡速度。
第 03 章部分：往返效率换算、单次套利收益分解、退化成本、价差阈值、需量电费节省、
            按计划曲线结算的电量收益、简单投资回收期。

约定：
- 功率 kW，电量 kWh，电价 元/kWh，时间 h（本模块是经济核算，时间用小时更直观）；
- 储能功率放电为正、充电为负（与全课程一致）；
- 效率用 0～1 的小数；
- 所有电价、成本参数都由调用方传入，本模块不内置任何地区的政策数值。
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

# ---------------------------------------------------------------------------
# 第 01 章：电网层面的直觉
# ---------------------------------------------------------------------------


def three_phase_line_loss_kw(p_kw: float, u_line_kv: float, r_ohm_per_phase: float, pf: float = 1.0) -> float:
    """三相平衡线路的有功损耗 = 3 × I² × R。

    I = P / (√3 × U线 × PF)，kW / kV 正好得到 A。
    化简后损耗 = P² × R / (U² × PF²)：输送功率不变时，电压翻倍、损耗降为 1/4。
    """
    if u_line_kv <= 0 or r_ohm_per_phase < 0 or not 0 < pf <= 1:
        raise ValueError("电压必须为正、电阻非负、功率因数在 (0, 1] 内")
    current_a = abs(p_kw) / (math.sqrt(3) * u_line_kv * pf)
    return 3.0 * current_a**2 * r_ohm_per_phase / 1000.0  # W → kW


def net_load(load: Sequence[float], pv: Sequence[float]) -> list[float]:
    """净负荷 = 负荷 − 新能源出力：剩下这部分才需要常规电源（和储能）来平衡。"""
    if len(load) != len(pv):
        raise ValueError("负荷与光伏序列长度不一致")
    return [l - p for l, p in zip(load, pv)]


@dataclass(frozen=True)
class LoadCurveStats:
    peak: float  # 最大负荷
    valley: float  # 最小负荷
    peak_valley_diff: float  # 峰谷差 = 峰 − 谷
    peak_valley_ratio: float  # 峰谷差率 = 峰谷差 / 峰
    load_factor: float  # 负荷率 = 平均 / 峰；越接近 1，设备利用越充分


def load_curve_stats(values: Sequence[float]) -> LoadCurveStats:
    """日负荷曲线的常用统计量（等间隔采样）。"""
    if not values:
        raise ValueError("序列为空")
    peak, valley = max(values), min(values)
    if peak <= 0:
        raise ValueError("峰值必须为正")
    diff = peak - valley
    return LoadCurveStats(peak, valley, diff, diff / peak, sum(values) / len(values) / peak)


def max_ramp_up_per_h(values: Sequence[float], dt_h: float) -> float:
    """相邻采样点之间的最大上升速度（单位/h）。鸭子曲线的“鸭脖子”就看它。"""
    if dt_h <= 0:
        raise ValueError("采样间隔必须为正")
    if len(values) < 2:
        return 0.0
    return max((b - a) / dt_h for a, b in zip(values[:-1], values[1:]))


# ---------------------------------------------------------------------------
# 第 03 章：效率换算
# ---------------------------------------------------------------------------


def _check_eta(eta: float) -> None:
    if not 0 < eta <= 1:
        raise ValueError(f"效率必须在 (0, 1] 内，收到 {eta}")


def round_trip_efficiency(e_dis_kwh: float, e_ch_kwh: float) -> float:
    """往返效率 = 放出电量 / 充入电量（同一计量点、同一 SOC 起止）。"""
    if e_ch_kwh <= 0 or e_dis_kwh < 0:
        raise ValueError("充电电量必须为正、放电电量非负")
    return e_dis_kwh / e_ch_kwh


def charge_energy_for_discharge(e_dis_kwh: float, eta_rt: float) -> float:
    """想放出 E_dis，要先充入 E_dis / η：损耗全部算在“多买的电”上。"""
    _check_eta(eta_rt)
    return e_dis_kwh / eta_rt


def one_way_to_round_trip(eta_ch: float, eta_dis: float) -> float:
    """单向效率 → 往返效率：两段损耗相乘，而不是相加。"""
    _check_eta(eta_ch)
    _check_eta(eta_dis)
    return eta_ch * eta_dis


def round_trip_to_one_way(eta_rt: float) -> float:
    """往返效率 → 单向效率（假设充、放两个方向效率相同）：开平方。"""
    _check_eta(eta_rt)
    return math.sqrt(eta_rt)


# ---------------------------------------------------------------------------
# 第 03 章：退化成本与套利
# ---------------------------------------------------------------------------


def degradation_cost_per_kwh(replacement_cost_yuan: float, cycle_life: float, kwh_per_cycle: float) -> float:
    """度电退化成本 = 电池重置成本 / 全寿命可放出电量（按放电电量折算）。

    这是“每放出 1 kWh，电池寿命被消耗掉多少钱”的线性近似。
    注意口径：这里按放电量折算；若按“充 + 放”双向吞吐量折算，数值约减半，
    但套利公式里乘的电量也要随之改变，两处口径必须一致。
    """
    if replacement_cost_yuan < 0 or cycle_life <= 0 or kwh_per_cycle <= 0:
        raise ValueError("成本非负，循环次数和每次电量必须为正")
    return replacement_cost_yuan / (cycle_life * kwh_per_cycle)


@dataclass(frozen=True)
class ArbitrageBreakdown:
    """一次“充 → 放”循环的收益分解（元）。"""

    e_dis_kwh: float  # 放电电量（计量点）
    e_ch_kwh: float  # 充电电量 = 放电电量 / 往返效率
    discharge_revenue: float  # 放电收入（或省下的高价电费）
    ideal_charge_cost: float  # 假设没有损耗时的充电成本 = E_dis × 充电电价
    efficiency_loss_cost: float  # 因效率损耗多买的电 = (E_ch − E_dis) × 充电电价
    degradation_cost: float  # 退化成本 = E_dis × 度电退化成本

    @property
    def charge_cost(self) -> float:
        return self.ideal_charge_cost + self.efficiency_loss_cost

    @property
    def gross_profit(self) -> float:
        """电费差（不含退化）：放电收入 − 充电成本。"""
        return self.discharge_revenue - self.charge_cost

    @property
    def net_profit(self) -> float:
        """净收益：再扣掉退化成本。这是决定“今天该不该充放”的口径。"""
        return self.gross_profit - self.degradation_cost


def arbitrage_cycle(
    e_dis_kwh: float, price_dis: float, price_ch: float, eta_rt: float, c_deg_per_kwh: float = 0.0
) -> ArbitrageBreakdown:
    """单次套利：收益 = E_dis × 放电电价 − (E_dis / η) × 充电电价 − E_dis × 度电退化成本。"""
    if e_dis_kwh < 0 or c_deg_per_kwh < 0:
        raise ValueError("放电电量和退化成本必须非负")
    e_ch = charge_energy_for_discharge(e_dis_kwh, eta_rt)
    return ArbitrageBreakdown(
        e_dis_kwh=e_dis_kwh,
        e_ch_kwh=e_ch,
        discharge_revenue=e_dis_kwh * price_dis,
        ideal_charge_cost=e_dis_kwh * price_ch,
        efficiency_loss_cost=(e_ch - e_dis_kwh) * price_ch,
        degradation_cost=e_dis_kwh * c_deg_per_kwh,
    )


def net_profit_per_kwh(price_dis: float, price_ch: float, eta_rt: float, c_deg_per_kwh: float = 0.0) -> float:
    """每放出 1 kWh 的净收益 = 放电电价 − 充电电价 / η − 度电退化成本。"""
    _check_eta(eta_rt)
    return price_dis - price_ch / eta_rt - c_deg_per_kwh


def breakeven_discharge_price(price_ch: float, eta_rt: float, c_deg_per_kwh: float = 0.0) -> float:
    """盈亏平衡放电电价：放电电价高于它才赚钱 = 充电电价 / η + 度电退化成本。"""
    _check_eta(eta_rt)
    return price_ch / eta_rt + c_deg_per_kwh


def breakeven_spread(price_ch: float, eta_rt: float, c_deg_per_kwh: float = 0.0) -> float:
    """盈亏平衡价差 = 充电电价 × (1/η − 1) + 度电退化成本。

    注意它依赖充电电价本身：同样的价差，充电电价越高，效率损失越贵。
    """
    return breakeven_discharge_price(price_ch, eta_rt, c_deg_per_kwh) - price_ch


def worth_cycling(
    price_dis: float, price_ch: float, eta_rt: float, c_deg_per_kwh: float = 0.0, margin_per_kwh: float = 0.0
) -> bool:
    """是否值得充放：每 kWh 净收益要超过安全裕度（覆盖预测误差、辅助用电等）。"""
    return net_profit_per_kwh(price_dis, price_ch, eta_rt, c_deg_per_kwh) > margin_per_kwh


# ---------------------------------------------------------------------------
# 第 03 章：其他收益与投资回收
# ---------------------------------------------------------------------------


def demand_charge_saving(demand_reduction_kw: float, demand_price_per_kw_month: float, months: int = 1) -> float:
    """需量电费节省 = 降低的最大需量 × 需量电价 × 月数。

    前提：整个计费周期里每一个需量窗口都压住了；只要有一个窗口没压住，当月节省可能大幅缩水（第 14 章）。
    """
    if demand_reduction_kw < 0 or demand_price_per_kw_month < 0 or months < 0:
        raise ValueError("参数必须非负")
    return demand_reduction_kw * demand_price_per_kw_month * months


def schedule_energy_revenue(p_bess_kw: Sequence[float], prices: Sequence[float], dt_h: float) -> float:
    """按计划曲线逐时段结算电量收益 = Σ P_BESS × 电价 × Δt。

    放电为正 → 收入为正；充电为负 → 自动变成成本。方向约定统一后，公式里不需要任何 if。
    """
    if len(p_bess_kw) != len(prices):
        raise ValueError("功率与电价序列长度不一致")
    if dt_h <= 0:
        raise ValueError("时段长度必须为正")
    return sum(p * c * dt_h for p, c in zip(p_bess_kw, prices))


def annual_net_cashflow(profit_per_cycle: float, cycles_per_year: float, om_cost_per_year: float = 0.0) -> float:
    """年净现金流 = 每次循环电费差 × 年循环次数 − 年运维费用。"""
    if cycles_per_year < 0 or om_cost_per_year < 0:
        raise ValueError("循环次数和运维费用必须非负")
    return profit_per_cycle * cycles_per_year - om_cost_per_year


def simple_payback_years(capex_yuan: float, annual_net_cashflow_yuan: float) -> float:
    """简单投资回收期 = 初始投资 / 年净现金流（不考虑折现、衰减和电价变化）。"""
    if capex_yuan < 0:
        raise ValueError("投资必须非负")
    if annual_net_cashflow_yuan <= 0:
        return math.inf  # 年现金流不为正，永远收不回
    return capex_yuan / annual_net_cashflow_yuan

