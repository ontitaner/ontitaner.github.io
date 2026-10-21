"""第 04、05 章：电池、BMS 与 SOC / SOH / SOP 能力模型。

约定（与附录 B 一致）：
- 功率 kW、电量 kWh、电流 A、电压 V、时间 s；SOC、SOH 在代码中用 0～1；
- 电池功率 / 电流：放电为正、充电为负（与 P_BESS 同向）；
- 可充 / 可放能力一律用非负幅值（available_charge_kw / available_discharge_kw）。

本模块中所有 *_TEACHING 表格和默认参数都是 [教学示例]，
现场以电芯规格书、BMS 定值单和项目配置为准。
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Mapping, Sequence

from .control import Hysteresis, interp_table


def _check_finite(**values: float) -> None:
    for name, v in values.items():
        if v is None or math.isnan(v):
            raise ValueError(f"{name} 无效（NaN/None），应在数据校验层拦截")


# ============================================================ 第 04 章：电芯与成组
@dataclass(frozen=True)
class PackRating:
    voltage_v: float     # 标称电压
    capacity_ah: float   # 容量（安时）
    energy_kwh: float    # 标称能量


def series_parallel(cell_voltage_v: float, cell_capacity_ah: float, n_series: int, n_parallel: int = 1) -> PackRating:
    """串联加电压、并联加容量；能量 = 电压 × 容量，与串并方式无关。"""
    if n_series < 1 or n_parallel < 1:
        raise ValueError("串联数和并联数至少为 1")
    v = cell_voltage_v * n_series
    ah = cell_capacity_ah * n_parallel
    return PackRating(voltage_v=v, capacity_ah=ah, energy_kwh=v * ah / 1000.0)


def c_rate(current_a: float, capacity_ah: float) -> float:
    """倍率 C = |电流| / 容量。0.5C 表示 2 小时充满或放完。"""
    if capacity_ah <= 0:
        raise ValueError("容量必须为正")
    return abs(current_a) / capacity_ah


def current_from_c_rate(c: float, capacity_ah: float) -> float:
    """由倍率求电流幅值（A）。"""
    if c < 0 or capacity_ah <= 0:
        raise ValueError("倍率必须非负、容量必须为正")
    return c * capacity_ah


def joule_heat_w(current_a: float, resistance_ohm: float) -> float:
    """内阻发热 I²R（W）：与电流的平方成正比，充电放电都发热。"""
    return current_a**2 * resistance_ohm


def terminal_voltage_v(ocv_v: float, current_a: float, resistance_ohm: float) -> float:
    """端电压 = 开路电压 − I·R。放电（I > 0）时端电压低于 OCV，充电时高于 OCV。"""
    return ocv_v - current_a * resistance_ohm


def bms_power_limit_kw(current_limit_a: float, voltage_v: float) -> float:
    """BMS 常以电流限值给出能力，换算成直流功率 P = I × U。"""
    if current_limit_a < 0 or voltage_v < 0:
        raise ValueError("电流限值和电压必须非负")
    return current_limit_a * voltage_v / 1000.0


def balancing_time_h(delta_soc: float, capacity_ah: float, balance_current_a: float) -> float:
    """把一个电芯的 SOC 差异 delta_soc（0～1）均衡掉需要多少小时。"""
    if balance_current_a <= 0:
        raise ValueError("均衡电流必须为正")
    return abs(delta_soc) * capacity_ah / balance_current_a


# ------------------------------------------------------------ OCV 曲线 [教学示例]
# 形状示意：LFP 在 30%～90% 之间非常平（约 1 mV / 1% SOC），三元（NCM）整体有明显斜率。
OCV_SOC_TEACHING = (0.00, 0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 0.95, 1.00)
LFP_OCV_TEACHING = (2.90, 3.10, 3.20, 3.25, 3.275, 3.29, 3.30, 3.31, 3.325, 3.33, 3.34, 3.36, 3.45)
NCM_OCV_TEACHING = (3.00, 3.40, 3.52, 3.60, 3.64, 3.68, 3.73, 3.80, 3.89, 3.98, 4.08, 4.13, 4.18)


def ocv_from_soc(soc: float, soc_pts: Sequence[float] = OCV_SOC_TEACHING,
                 v_pts: Sequence[float] = LFP_OCV_TEACHING) -> float:
    """查 OCV-SOC 表：给定 SOC 求静置电压。"""
    return interp_table(soc, soc_pts, v_pts)


def soc_from_ocv(v: float, soc_pts: Sequence[float] = OCV_SOC_TEACHING,
                 v_pts: Sequence[float] = LFP_OCV_TEACHING) -> float:
    """反查：给定静置电压求 SOC（OCV 校准）。要求电压表严格递增。"""
    return interp_table(v, v_pts, soc_pts)


def ocv_slope_v_per_soc(soc: float, soc_pts: Sequence[float] = OCV_SOC_TEACHING,
                        v_pts: Sequence[float] = LFP_OCV_TEACHING, h: float = 0.001) -> float:
    """OCV 曲线在 soc 处的斜率（V / 单位 SOC）。1 mV/1% 对应 0.1 V/单位 SOC。"""
    lo, hi = max(soc - h, soc_pts[0]), min(soc + h, soc_pts[-1])
    return (ocv_from_soc(hi, soc_pts, v_pts) - ocv_from_soc(lo, soc_pts, v_pts)) / (hi - lo)


def soc_error_from_voltage_error(dv_v: float, soc: float, soc_pts: Sequence[float] = OCV_SOC_TEACHING,
                                 v_pts: Sequence[float] = LFP_OCV_TEACHING) -> float:
    """电压测量误差 dv_v 会造成多大的 OCV 校准误差（0～1）。曲线越平，误差越大。"""
    slope = ocv_slope_v_per_soc(soc, soc_pts, v_pts)
    if slope <= 0:
        raise ValueError("OCV 曲线斜率必须为正")
    return abs(dv_v) / slope


# ------------------------------------------------------------ 温度 → 允许倍率 [教学示例]
# 低温对“充电”的限制比“放电”严格得多：低温充电容易析锂（第 04 章 4.7）。
CHARGE_C_TABLE_TEACHING = ((-20, 0, 5, 10, 15, 45, 50, 55), (0.0, 0.0, 0.1, 0.25, 0.5, 0.5, 0.2, 0.0))
DISCHARGE_C_TABLE_TEACHING = ((-30, -20, -10, 0, 10, 45, 50, 55, 60), (0.0, 0.2, 0.3, 0.4, 0.5, 0.5, 0.3, 0.15, 0.0))


def temperature_c_limits(temp_c: float, charge_table=CHARGE_C_TABLE_TEACHING,
                         discharge_table=DISCHARGE_C_TABLE_TEACHING) -> tuple[float, float]:
    """按电芯温度查允许倍率，返回 (可充倍率, 可放倍率)。充放电是两张独立的表。"""
    _check_finite(temp_c=temp_c)
    return interp_table(temp_c, *charge_table), interp_table(temp_c, *discharge_table)


# ------------------------------------------------------------ BMS 上送数据的合理性校验
@dataclass(frozen=True)
class BmsReport:
    """EMS 从 BMS（堆级管理单元）读到的关键数据，已在接入层换算成本课程约定。"""
    soc: float
    soh: float
    available_charge_kw: float
    available_discharge_kw: float
    charge_allowed: bool = True
    discharge_allowed: bool = True
    max_cell_v: float = math.nan
    min_cell_v: float = math.nan
    max_cell_temp_c: float = math.nan
    min_cell_temp_c: float = math.nan
    age_s: float = 0.0   # 数据年龄：现在 − BMS 数据时间戳


@dataclass(frozen=True)
class BmsCheck:
    available_charge_kw: float
    available_discharge_kw: float
    issues: tuple[str, ...]


def _check_one_direction(name: str, value: float, allowed: bool, plausible_max: float, issues: list[str]) -> float:
    if value is None or math.isnan(value):
        issues.append(f"可{name}功率无效（NaN），按不可{name}处理")
        return 0.0
    if value < 0:
        issues.append(f"可{name}功率为负（{value}），检查接入层符号约定，按不可{name}处理")
        return 0.0
    if value > plausible_max:
        issues.append(f"可{name}功率 {value} 超出物理上限 {plausible_max}，疑似缩放系数错误，按不可{name}处理")
        return 0.0
    if not allowed:
        if value > 0:
            issues.append(f"禁{name}标志置位但可{name}功率为 {value}，以禁止标志为准")
        return 0.0
    return value  # 合理：原样使用，不再重复降额


def check_bms_report(report: BmsReport, plausible_max_charge_kw: float, plausible_max_discharge_kw: float,
                     max_age_s: float = 5.0) -> BmsCheck:
    """校验 BMS 上送数据，返回 EMS 可以使用的可充/可放能力和问题清单。

    原则：BMS 算好的能力，合理就原样使用（不再按温度、SOC 重复降额）；
    不合理（超时、NaN、负数、超出物理上限、与禁止标志矛盾）就取保守值 0 并告警。
    """
    issues: list[str] = []
    if report.age_s > max_age_s:
        return BmsCheck(0.0, 0.0, (f"BMS 数据超时 {report.age_s:.1f} s（上限 {max_age_s} s），按不可充不可放处理",))
    chg = _check_one_direction("充", report.available_charge_kw, report.charge_allowed, plausible_max_charge_kw, issues)
    dis = _check_one_direction("放", report.available_discharge_kw, report.discharge_allowed,
                               plausible_max_discharge_kw, issues)
    if math.isnan(report.soc) or not 0.0 <= report.soc <= 1.0:
        issues.append(f"SOC 越界（{report.soc}），能量类计算不可信")
    if not (math.isnan(report.max_cell_v) or math.isnan(report.min_cell_v)) and report.min_cell_v > report.max_cell_v:
        issues.append("最低单体电压大于最高单体电压，点位可能接反")
    if not (math.isnan(report.max_cell_temp_c) or math.isnan(report.min_cell_temp_c)) \
            and report.min_cell_temp_c > report.max_cell_temp_c:
        issues.append("最低单体温度大于最高单体温度，点位可能接反")
    return BmsCheck(chg, dis, tuple(issues))


# ------------------------------------------------------------ 簇间不一致：木桶效应
@dataclass(frozen=True)
class StackEnergy:
    dischargeable_kwh: float        # 等电流并联：最低簇到下限即整堆停放
    chargeable_kwh: float           # 等电流并联：最高簇到上限即整堆停充
    ideal_dischargeable_kwh: float  # 理想：每簇都能各自用到下限
    ideal_chargeable_kwh: float


def stack_energy(socs: Sequence[float], capacity_kwh_each: float, soc_min: float, soc_max: float) -> StackEnergy:
    """多簇并联、各簇容量相同、电流均分时的可充/可放电量（电池内部储能口径，不含效率）。

    放电看最低簇，充电看最高簇，这就是“木桶效应”。
    """
    if not socs:
        raise ValueError("至少需要一个簇")
    n = len(socs)
    dis = n * max(0.0, min(socs) - soc_min) * capacity_kwh_each
    chg = n * max(0.0, soc_max - max(socs)) * capacity_kwh_each
    ideal_dis = sum(max(0.0, s - soc_min) for s in socs) * capacity_kwh_each
    ideal_chg = sum(max(0.0, soc_max - s) for s in socs) * capacity_kwh_each
    return StackEnergy(dis, chg, ideal_dis, ideal_chg)


def stack_power_limit_kw(cluster_limits_kw: Sequence[float]) -> float:
    """电流均分假设下，堆级能力 = 最弱簇能力 × 簇数（而不是各簇之和）。"""
    if not cluster_limits_kw:
        raise ValueError("至少需要一个簇")
    return min(cluster_limits_kw) * len(cluster_limits_kw)


# ============================================================ 第 05 章：SOC 与效率
@dataclass(frozen=True)
class SocUpdate:
    soc: float                 # 施加边界后的 SOC，用于后续状态
    soc_raw: float             # 未施加边界的计算结果，越界时必须记录
    violated: bool
    reason: str | None         # "above_max" / "below_min" / None
    stored_delta_kwh: float    # 电池内部储能变化，充电为正


def update_soc(soc: float, p_kw: float, dt_s: float, capacity_kwh: float,
               eta_charge: float = 1.0, eta_discharge: float = 1.0,
               soc_min: float = 0.0, soc_max: float = 1.0) -> SocUpdate:
    """SOC 离散更新（能量口径），p_kw 放电为正。

    - 放电：要从电池里拿出 P·dt / η 的能量，外部才能收到 P·dt，所以“除以效率”；
    - 充电：外部送进 |P|·dt，只有 |P|·dt·η 真正存进去，所以“乘以效率”；
    - η 必须和 p_kw 的测量平面对应：p_kw 在直流侧就用电池效率，在交流侧就用“电池 × PCS”效率。
    越界时不静默吞掉：soc_raw 和 reason 交给调用方记录事件。
    """
    _check_finite(soc=soc, p_kw=p_kw, dt_s=dt_s)
    if capacity_kwh <= 0:
        raise ValueError("容量必须为正")
    if not (0 < eta_charge <= 1 and 0 < eta_discharge <= 1):
        raise ValueError("效率必须在 (0, 1] 之间")
    if dt_s < 0:
        raise ValueError("dt 必须非负")
    if soc_min >= soc_max:
        raise ValueError("soc_min 必须小于 soc_max")
    hours = dt_s / 3600.0
    if p_kw >= 0:
        stored_delta = -p_kw * hours / eta_discharge
    else:
        stored_delta = -p_kw * hours * eta_charge  # -p_kw 为正：充电幅值
    raw = soc + stored_delta / capacity_kwh
    if raw > soc_max:
        return SocUpdate(soc_max, raw, True, "above_max", stored_delta)
    if raw < soc_min:
        return SocUpdate(soc_min, raw, True, "below_min", stored_delta)
    return SocUpdate(raw, raw, False, None, stored_delta)


def round_trip_efficiency(charge_chain: Sequence[float], discharge_chain: Sequence[float]) -> float:
    """往返效率 RTE = 充电路径各环节效率之积 × 放电路径各环节效率之积。"""
    etas = list(charge_chain) + list(discharge_chain)
    if not etas or any(not 0 < e <= 1 for e in etas):
        raise ValueError("效率必须在 (0, 1] 之间")
    return math.prod(etas)


def actual_capacity_kwh(rated_kwh: float, soh: float) -> float:
    """当前实际容量 = 额定容量 × SOH（容量口径）。"""
    if rated_kwh <= 0 or not 0 < soh <= 1.2:
        raise ValueError("额定容量必须为正，SOH 应在合理范围内")
    return rated_kwh * soh


def dischargeable_energy_kwh(soc: float, capacity_kwh: float, soc_min: float, eta_discharge: float = 1.0) -> float:
    """从当前 SOC 放到 soc_min，外部（效率所在的测量平面）能收到多少电量。"""
    return max(0.0, soc - soc_min) * capacity_kwh * eta_discharge


def chargeable_energy_kwh(soc: float, capacity_kwh: float, soc_max: float, eta_charge: float = 1.0) -> float:
    """从当前 SOC 充到 soc_max，外部需要送进多少电量。"""
    return max(0.0, soc_max - soc) * capacity_kwh / eta_charge


# ------------------------------------------------------------ 安时积分
def ah_drift_soc(bias_a: float, hours: float, capacity_ah: float) -> float:
    """电流传感器零点偏差 bias_a 持续 hours 小时造成的 SOC 误差（0～1）。"""
    return abs(bias_a) * hours / capacity_ah


class CoulombCounter:
    """安时积分 SOC 估计器（教学版，对应正文 5.3）。current_a 放电为正。

    公式：SOC[k] = SOC[k-1] − I[k]·Δt / (3600·C)，充电时 I 再乘库仑效率 η_c。
    只会“累加”，不会自己发现误差：需要 OCV / 满充 / 满放校准把它拉回来（5.4）。
    """

    def __init__(self, capacity_ah: float, soc0: float, coulomb_eff_charge: float = 1.0):
        """capacity_ah：C，当前实际容量（Ah），不是额定容量（5.2）；
        soc0：SOC[0]，初始 SOC（0～1），初值错了会一直错到下次校准；
        coulomb_eff_charge：η_c，充电库仑效率（0～1），1.0 表示理想无损。
        """
        if capacity_ah <= 0:
            raise ValueError("容量必须为正")  # C 是分母，≤0 会除零或让 SOC 方向反转
        self.capacity_ah = capacity_ah
        self.soc = soc0
        self.coulomb_eff_charge = coulomb_eff_charge
        self.throughput_ah = 0.0  # 自上次校准以来的累计吞吐量，越大说明误差风险越高

    def update(self, current_a: float, dt_s: float) -> float:
        """推进一步安时积分，返回新的 SOC。

        current_a：I[k]，本步电流（A），放电为正、充电为负；
        dt_s：Δt，本步时长（s）。
        """
        _check_finite(current_a=current_a)  # NaN 电流会污染后续所有 SOC，入口就拦截
        ah = current_a * dt_s / 3600.0      # 本步流过的电荷（Ah）：÷3600 把“安·秒”换成“安时”
        if current_a < 0:
            ah *= self.coulomb_eff_charge   # 充电：只有 η_c 比例的电荷真正存进电池
        # 一个减号管两个方向：放电 ah>0 → SOC 下降；充电 ah<0 → SOC 上升。
        # 限制在 0～1 与真实 BMS 显示一致；越界信息在此被丢弃（仿真中应改用 update_soc 保留 soc_raw）
        self.soc = min(1.0, max(0.0, self.soc - ah / self.capacity_ah))
        # 吞吐量不分方向累加，衡量“攒了多少误差风险”，校准时清零
        self.throughput_ah += abs(current_a) * dt_s / 3600.0
        return self.soc

    def calibrate(self, soc: float) -> None:
        """用 OCV 或满充/满放判据得到的 SOC 覆盖积分结果（5.4）。

        校准相当于事件溯源里的“打快照”：丢弃累积误差，从可信值重新开始积分。
        """
        self.soc = soc
        self.throughput_ah = 0.0  # 误差风险随校准归零


# ------------------------------------------------------------ 簇级 SOC 聚合
def aggregate_soc(socs: Sequence[float], method: str = "mean", capacities_kwh: Sequence[float] | None = None) -> float:
    """把各簇 SOC 汇总成堆级 SOC。

    - "min"：放电规划用，保守；
    - "max"：充电规划用，保守；
    - "mean"：算术平均，只在各簇容量相同时有能量含义；
    - "weighted"：按容量加权，等于“总剩余电量 / 总容量”。
    """
    if not socs:
        raise ValueError("至少需要一个簇")
    if method == "min":
        return min(socs)
    if method == "max":
        return max(socs)
    if method == "mean":
        return sum(socs) / len(socs)
    if method == "weighted":
        if capacities_kwh is None or len(capacities_kwh) != len(socs) or sum(capacities_kwh) <= 0:
            raise ValueError("加权平均需要与 SOC 等长、总和为正的容量列表")
        return sum(s * c for s, c in zip(socs, capacities_kwh)) / sum(capacities_kwh)
    raise ValueError(f"未知聚合方法：{method}")


# ------------------------------------------------------------ SOC 分区与滞回
@dataclass(frozen=True)
class SocZones:
    """SOC 分区阈值（0～1），默认值为 [教学示例]。从低到高必须严格递增。"""
    hard_min: float = 0.03     # 硬保护下限：到这里 BMS 可能已动作，EMS 规划永远不应到达
    op_min: float = 0.10       # 运行下限：EMS 停止放电
    warn_min: float = 0.15     # 预警下限：开始告警、放电降额
    target_low: float = 0.45   # 目标区间（调频备用、自恢复的目标）
    target_high: float = 0.55
    warn_max: float = 0.85
    op_max: float = 0.90
    hard_max: float = 0.97

    def __post_init__(self):
        seq = [self.hard_min, self.op_min, self.warn_min, self.target_low,
               self.target_high, self.warn_max, self.op_max, self.hard_max]
        if any(b <= a for a, b in zip(seq, seq[1:])) or seq[0] < 0 or seq[-1] > 1:
            raise ValueError(f"SOC 分区阈值必须在 0～1 内严格递增：{seq}")


def classify_soc(soc: float, z: SocZones) -> str:
    """返回 SOC 所在分区。下侧用“小于”、上侧用“大于”判定：正好等于阈值时归入内侧分区。

    例：SOC 正好等于 op_min 属于 "warn_low"，此时 soc_window_factors 给出的放电比例已经是 0。
    """
    _check_finite(soc=soc)
    if soc < z.hard_min:
        return "hard_low"
    if soc < z.op_min:
        return "stop_low"
    if soc < z.warn_min:
        return "warn_low"
    if soc > z.hard_max:
        return "hard_high"
    if soc > z.op_max:
        return "stop_high"
    if soc > z.warn_max:
        return "warn_high"
    if z.target_low <= soc <= z.target_high:
        return "target"
    return "normal"


def soc_window_factors(soc: float, z: SocZones) -> tuple[float, float]:
    """EMS 自己的 SOC 运行窗口带来的功率比例，返回 (充电比例, 放电比例)。

    放电：运行下限处为 0，预警下限处为 1，中间线性；充电对称。
    这是 EMS 的运行策略（留备用、延寿），不是在重复 BMS 的安全降额。
    """
    dis = interp_table(soc, [z.op_min, z.warn_min], [0.0, 1.0])
    chg = interp_table(soc, [z.warn_max, z.op_max], [1.0, 0.0])
    return chg, dis


class SocPermissionGate:
    """带滞回的充/放电许可：到运行限值就禁止，离开限值 band 以上才恢复，防止启停抖动。"""

    def __init__(self, zones: SocZones, band: float = 0.02,
                 charge_blocked: bool = False, discharge_blocked: bool = False):
        if band <= 0:
            raise ValueError("滞回带宽必须为正")
        # 放电：SOC 低于 op_min 时“禁止”被打开，高于 op_min + band 才关闭
        self._block_dis = Hysteresis(on_below=zones.op_min, off_above=zones.op_min + band,
                                     initial=discharge_blocked)
        # 充电方向相反：对 −SOC 使用同一个滞回类
        self._block_chg = Hysteresis(on_below=-zones.op_max, off_above=-(zones.op_max - band),
                                     initial=charge_blocked)

    def update(self, soc: float) -> tuple[bool, bool]:
        """返回 (允许充电, 允许放电)。"""
        return (not self._block_chg.update(-soc), not self._block_dis.update(soc))


def soc_window_limits_kw(soc: float, zones: SocZones, rated_charge_kw: float, rated_discharge_kw: float,
                         gate: SocPermissionGate | None = None) -> tuple[float, float]:
    """EMS SOC 窗口对应的 (可充, 可放) 功率上限，作为能力模型中的一项。"""
    chg_f, dis_f = soc_window_factors(soc, zones)
    if gate is not None:
        chg_ok, dis_ok = gate.update(soc)
        chg_f *= chg_ok
        dis_f *= dis_ok
    return rated_charge_kw * chg_f, rated_discharge_kw * dis_f


# ------------------------------------------------------------ SOP 与能力模型
def ac_limits_from_dc(charge_dc_kw: float, discharge_dc_kw: float, eta_pcs: float) -> tuple[float, float]:
    """把 BMS 的直流侧能力换算到 PCS 交流侧，返回 (可充 AC, 可放 AC)。

    放电：直流侧放出 P，交流侧只收到 P × η；
    充电：要让直流侧收到 P，交流侧得吸收 P / η。
    """
    if not 0 < eta_pcs <= 1:
        raise ValueError("效率必须在 (0, 1] 之间")
    if charge_dc_kw < 0 or discharge_dc_kw < 0:
        raise ValueError("能力必须是非负幅值")
    return charge_dc_kw / eta_pcs, discharge_dc_kw * eta_pcs


def energy_limited_power_kw(energy_kwh: float, duration_s: float) -> float:
    """要持续 duration_s 秒，平均功率最多是 电量 / 时长。"""
    if duration_s <= 0:
        raise ValueError("持续时间必须为正")
    return max(0.0, energy_kwh) / (duration_s / 3600.0)


def sop_for_duration(p_instant_kw: float, energy_kwh: float, duration_s: float) -> float:
    """与持续时间相关的 SOP：取“瞬时功率能力”和“电量能支撑的平均功率”中的小者。"""
    return min(p_instant_kw, energy_limited_power_kw(energy_kwh, duration_s))


@dataclass(frozen=True)
class Capability:
    available_charge_kw: float
    available_discharge_kw: float
    charge_limited_by: str
    discharge_limited_by: str


def min_with_reason(limits: Mapping[str, float]) -> tuple[float, str]:
    """多个限值取最小，并返回是谁在限。并列时取先登记的一项（按优先级登记）。"""
    if not limits:
        raise ValueError("至少需要一个限值")
    for name, v in limits.items():
        if v is None or math.isnan(v):
            raise ValueError(f"限值 {name} 为 NaN，应在数据校验层处理")
        if v < 0:
            raise ValueError(f"限值 {name} 为负（{v}），能力必须是非负幅值")
    name, value = min(limits.items(), key=lambda kv: kv[1])
    return value, name


def combine_capability(charge_limits: Mapping[str, float], discharge_limits: Mapping[str, float]) -> Capability:
    """充、放两个方向分别取最小值，得到 EMS 本周期使用的可用能力。"""
    chg, chg_by = min_with_reason(charge_limits)
    dis, dis_by = min_with_reason(discharge_limits)
    return Capability(chg, dis, chg_by, dis_by)

