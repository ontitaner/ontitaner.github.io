"""第 06 章：PCS 的真实能力与指令修正。

约定（附录 B）：P 放电为正、充电为负；Q 向电网发出为正；
电压为交流侧线电压有效值 V，电流 A，功率 kW / kvar / kVA，温度 °C。

本模块是“EMS 眼中的 PCS 能力模型”：用铭牌、电流上限、降额表近似厂商能力曲线。
它不是 PCS 内部控制算法，现场以厂商能力曲线和技术协议为准。
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Mapping, Sequence

from .control import clamp, interp_table

SQRT3 = math.sqrt(3.0)


# ---------------------------------------------------------------- 电压、电流与容量
def apparent_from_current_kva(u_line_v: float, i_a: float) -> float:
    """三相视在功率 S = √3 × 线电压 × 相电流（结果换算为 kVA）。"""
    if u_line_v < 0 or i_a < 0:
        raise ValueError("电压、电流必须非负")
    return SQRT3 * u_line_v * i_a / 1000.0


def current_from_apparent_a(s_kva: float, u_line_v: float) -> float:
    """给定视在功率和线电压，反算相电流 I = S / (√3 × U)。"""
    if u_line_v <= 0:
        raise ValueError("线电压必须为正")
    return s_kva * 1000.0 / (SQRT3 * u_line_v)


def dc_limited_power_kw(u_dc_v: float, i_dc_max_a: float) -> float:
    """直流侧电流上限决定的功率上限 P = U_dc × I_dc_max。

    电池电压随 SOC 下降而降低，同样的电流上限下能输送的功率就变小，
    这是放电末段“能力缩水”的常见原因之一。
    """
    if u_dc_v < 0 or i_dc_max_a < 0:
        raise ValueError("电压、电流必须非负")
    return u_dc_v * i_dc_max_a / 1000.0


# ---------------------------------------------------------------- 铭牌与降额
@dataclass(frozen=True)
class PcsRating:
    """PCS 铭牌与能力参数。数值应来自厂商数据表，课程示例均为 [教学示例]。"""

    s_rated_kva: float  # 铭牌视在容量
    u_rated_v: float  # 交流侧额定线电压
    i_max_a: float | None = None  # 交流侧最大持续电流；None 表示等于额定电流（没有电流裕量）
    p_discharge_max_kw: float | None = None  # 放电有功上限；None 表示只受视在容量限制
    p_charge_max_kw: float | None = None  # 充电有功上限（非负幅值）；None 同上
    q_max_kvar: float | None = None  # 无功上限（非负幅值）；None 同上
    derate_temp_c: Sequence[float] = (45.0, 55.0, 60.0)  # 温度降额表：温度点
    derate_ratio: Sequence[float] = (1.0, 0.8, 0.0)  # 温度降额表：可用比例

    @property
    def rated_current_a(self) -> float:
        return current_from_apparent_a(self.s_rated_kva, self.u_rated_v)

    @property
    def max_current_a(self) -> float:
        return self.rated_current_a if self.i_max_a is None else self.i_max_a


def temperature_derate_ratio(rating: PcsRating, temp_c: float) -> float:
    """按厂商降额表查当前温度下的可用比例（表外取端点值，不外推）。"""
    return interp_table(temp_c, rating.derate_temp_c, rating.derate_ratio)


def available_apparent_kva(rating: PcsRating, u_line_v: float, temp_c: float) -> float:
    """当前工况下 PCS 可用的视在容量。

    1) 电流上限：S_cur = √3 × U × I_max，电压偏低时它会小于铭牌容量；
    2) 铭牌上限：电压偏高时电流没到上限，但仍不能超过 S_rated；
    3) 温度降额：再乘以降额比例。
    不同厂商的降额口径不同（有的降电流、有的降功率），这里用乘法作教学近似。
    """
    s_cur = apparent_from_current_kva(u_line_v, rating.max_current_a)
    return min(rating.s_rated_kva, s_cur) * temperature_derate_ratio(rating, temp_c)


# ---------------------------------------------------------------- 有功/无功分配
@dataclass
class PQResult:
    p_kw: float
    q_kvar: float
    p_unserved_kw: float  # 请求值 − 实际可执行值（带方向）
    q_unserved_kvar: float
    reasons: list[str] = field(default_factory=list)


def allocate_pq(
    p_req_kw: float,
    q_req_kvar: float,
    s_avail_kva: float,
    p_charge_max_kw: float | None = None,
    p_discharge_max_kw: float | None = None,
    q_max_kvar: float | None = None,
    priority: str = "P",
) -> PQResult:
    """把 (P, Q) 请求压回能力边界，并记录没满足的部分和原因。

    priority="P"：有功优先，先保 P，剩余容量给 Q（Q_max = √(S² − P²)）；
    priority="Q"：无功优先，先保 Q，剩余容量给 P。
    """
    if s_avail_kva < 0:
        raise ValueError("可用视在容量必须非负")
    if priority not in ("P", "Q"):
        raise ValueError("priority 只能是 'P' 或 'Q'")
    if any(v is not None and v < 0 for v in (p_charge_max_kw, p_discharge_max_kw, q_max_kvar)):
        raise ValueError("充/放/无功上限必须是非负幅值")
    s = s_avail_kva
    reasons: list[str] = []

    # 第 1 步：按充/放方向的有功上限、无功上限截断（上限都是非负幅值）
    p_lo = -(s if p_charge_max_kw is None else min(s, p_charge_max_kw))
    p_hi = s if p_discharge_max_kw is None else min(s, p_discharge_max_kw)
    q_lim = s if q_max_kvar is None else min(s, q_max_kvar)
    p1 = clamp(p_req_kw, p_lo, p_hi)
    q1 = clamp(q_req_kvar, -q_lim, q_lim)
    if p1 != p_req_kw:
        reasons.append("有功超出充/放方向上限")
    if q1 != q_req_kvar:
        reasons.append("无功超出无功上限")

    # 第 2 步：P、Q 共享同一个视在容量，按优先级分配
    if priority == "P":
        p = p1
        q_cap = math.sqrt(max(0.0, s * s - p * p))
        q = clamp(q1, -q_cap, q_cap)
        if q != q1:
            reasons.append("有功优先：视在容量不足，无功被压缩")
    else:
        q = q1
        p_cap = math.sqrt(max(0.0, s * s - q * q))
        p = clamp(p1, -p_cap, p_cap)
        if p != p1:
            reasons.append("无功优先：视在容量不足，有功被压缩")

    return PQResult(p, q, p_req_kw - p, q_req_kvar - q, reasons)


def apply_pcs_limits(
    p_cmd_kw: float,
    q_cmd_kvar: float,
    rating: PcsRating,
    u_line_v: float,
    temp_c: float,
    priority: str = "P",
    running: bool = True,
) -> PQResult:
    """模拟 PCS 收到 EMS 设定值后“拒绝或修正”的行为（教学近似）。

    - 不在运行状态（停机、故障、待机）：拒绝，输出 0；
    - 在运行状态：按电压、温度算出可用容量，再按优先级修正。
    EMS 必须读回实际值，而不是假设设定值已被执行。
    """
    if not running:
        return PQResult(0.0, 0.0, p_cmd_kw, q_cmd_kvar, ["PCS 未处于运行状态，拒绝执行"])
    s_avail = available_apparent_kva(rating, u_line_v, temp_c)
    result = allocate_pq(
        p_cmd_kw,
        q_cmd_kvar,
        s_avail,
        rating.p_charge_max_kw,
        rating.p_discharge_max_kw,
        rating.q_max_kvar,
        priority,
    )
    if s_avail < rating.s_rated_kva:
        result.reasons.insert(0, f"可用容量降至 {s_avail:.0f} kVA（电压/温度降额）")
    return result


def pq_boundary(
    s_kva: float,
    p_charge_max_kw: float | None = None,
    p_discharge_max_kw: float | None = None,
    n: int = 721,
) -> tuple[list[float], list[float]]:
    """能力边界曲线：视在容量圆与充/放有功上限的交集，用于画图和可视化校核。"""
    p_lo = -s_kva if p_charge_max_kw is None else -min(s_kva, p_charge_max_kw)
    p_hi = s_kva if p_discharge_max_kw is None else min(s_kva, p_discharge_max_kw)
    ps, qs = [], []
    for k in range(n):
        theta = 2 * math.pi * k / (n - 1)
        ps.append(clamp(s_kva * math.cos(theta), p_lo, p_hi))
        qs.append(s_kva * math.sin(theta))
    return ps, qs


# ---------------------------------------------------------------- 状态字/故障字
def decode_bits(word: int, bit_names: Mapping[int, str]) -> list[str]:
    """把 PCS 上送的状态字/故障字按位解析成名称列表（位号从 0 开始）。

    位定义以厂商点表为准；未在表中定义但置 1 的位也要报出来，避免“静默丢故障”。
    """
    if word < 0:
        raise ValueError("状态字必须是非负整数（先按点表把寄存器转成无符号数）")
    active = []
    bit = 0
    while word >> bit:
        if (word >> bit) & 1:
            active.append(bit_names.get(bit, f"未定义位 bit{bit}"))
        bit += 1
    return active

