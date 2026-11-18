"""第 17 章：无功电压——电压降近似、Q-U 下垂、PF→Q、P-Q 圆投影（三种优先策略）。

约定（附录 B）：Q_BESS 向电网**发出无功为正**、吸收为负；电压低 → 发出无功（正）。
P 放电为正。单位：kW、kvar、kVA、kV、V、Ω；电压标幺值 pu。
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from .control import clamp, deadband_cut, deadband_shift


# ================================================================ 电压降近似
def voltage_rise_v(p_kw: float, q_kvar: float, r_ohm: float, x_ohm: float, u_kv: float) -> float:
    """电源经线路向电网送出 (P, Q) 时，送出端相对电网侧的电压抬升 ΔU ≈ (P·R + Q·X) / U。

    单位巧合：kW·Ω / kV = V，所以结果直接是伏特（线电压）。
    反过来，负荷从电网取 (P, Q) 时，负荷端电压**降低**同样的量。
    这是忽略横向分量的近似，适用于 ΔU 占 U 的比例较小（几个百分点）的情况。
    """
    if u_kv <= 0:
        raise ValueError("电压必须为正")
    return (p_kw * r_ohm + q_kvar * x_ohm) / u_kv


def q_for_voltage_change_kvar(delta_u_v: float, x_ohm: float, u_kv: float) -> float:
    """要把本地电压抬高 ΔU（伏），大约需要多发出多少无功：ΔQ ≈ ΔU · U / X。"""
    if x_ohm <= 0 or u_kv <= 0:
        raise ValueError("电抗和电压必须为正")
    return delta_u_v * u_kv / x_ohm


def voltage_deviation_pct(u_meas_kv: float, u_nominal_kv: float) -> float:
    """电压偏差（%）=（实测 − 标称）/ 标称 × 100。"""
    if u_nominal_kv <= 0:
        raise ValueError("标称电压必须为正")
    return (u_meas_kv - u_nominal_kv) / u_nominal_kv * 100.0


# ================================================================ 控制模式
def q_from_pf(p_kw: float, pf: float, q_sign: int) -> float:
    """定功率因数：Q = sign × |P| × tan(arccos PF)。

    PF 只是幅值（0～1]，方向必须由 q_sign 明确给出：+1 发出、−1 吸收。
    “超前/滞后”对应哪个符号取决于厂家和参考方向（发电机惯例还是负荷惯例），按项目核对后再映射成 q_sign。
    """
    if not 0 < pf <= 1:
        raise ValueError(f"功率因数幅值必须在 (0, 1]：{pf}")
    if q_sign not in (1, -1):
        raise ValueError("q_sign 只能是 +1（发出）或 −1（吸收）")
    return q_sign * abs(p_kw) * math.tan(math.acos(pf))


def pf_signed(p_kw: float, q_kvar: float) -> tuple[float, str]:
    """返回 (PF 幅值, "发出"/"吸收"/"无")，避免只用一个带符号的 PF 表达两种含义。"""
    s = math.hypot(p_kw, q_kvar)
    pf = 1.0 if s == 0 else abs(p_kw) / s
    return pf, ("发出" if q_kvar > 0 else "吸收" if q_kvar < 0 else "无")


@dataclass
class QuDroopConfig:
    q_max_kvar: float  # 下垂输出限幅（非负幅值）
    slope_kvar_per_pu: float  # 电压每偏差 1 pu，无功变化多少（正数）
    deadband_pu: float = 0.01  # [教学示例]
    u_ref_pu: float = 1.0
    deadband_mode: str = "shift"  # "shift" 连续型 / "cut" 截断型


def qu_droop_kvar(u_pu: float, cfg: QuDroopConfig) -> float:
    """Q-U 下垂：电压低 → 发出无功（正）；电压高 → 吸收无功（负）。"""
    if cfg.q_max_kvar < 0 or cfg.slope_kvar_per_pu <= 0:
        raise ValueError("限幅必须非负、斜率必须为正")
    du = u_pu - cfg.u_ref_pu
    if cfg.deadband_mode == "shift":
        eff = deadband_shift(du, cfg.deadband_pu)
    elif cfg.deadband_mode == "cut":
        eff = deadband_cut(du, cfg.deadband_pu)
    else:
        raise ValueError(f"未知死区类型：{cfg.deadband_mode}")
    return clamp(-cfg.slope_kvar_per_pu * eff, -cfg.q_max_kvar, cfg.q_max_kvar)  # 负号决定方向


# ================================================================ AVC 定电压闭环
@dataclass
class AvcStep:
    """一次 AVC 计算的可审计结果。"""
    q_requested_kvar: float
    error_pu: float
    integral_kvar: float
    saturated: bool
    enabled: bool
    reason: str


class AvcController:
    """教学级 AVC 子站内环：用 PI 让 PCC 电压跟踪目标，并在无功能力顶住时冻结积分。

    这不是完整现场 AVC：不含远动规约、PCS/SVG 多设备分配、OLTC 协调或方向反常闭锁。
    调用者应传入本拍可用无功范围；测量无效时本控制器冻结积分并不产生新请求。
    """

    def __init__(self, u_target_pu: float, kp_kvar_per_pu: float, ki_kvar_per_pu_s: float):
        if kp_kvar_per_pu < 0 or ki_kvar_per_pu_s < 0:
            raise ValueError("PI 增益必须非负")
        self.u_target_pu = u_target_pu
        self.kp_kvar_per_pu = kp_kvar_per_pu
        self.ki_kvar_per_pu_s = ki_kvar_per_pu_s
        self.integral_kvar = 0.0

    def reset(self, integral_kvar: float = 0.0) -> None:
        """模式切换或人工接管后按当前工况重新初始化积分。"""
        self.integral_kvar = integral_kvar

    def update(self, u_meas_pu: float | None, dt_s: float, q_min_kvar: float, q_max_kvar: float,
               valid: bool = True) -> AvcStep:
        """输入 PCC 电压与本拍可用 Q 范围，输出请求 Q；电压高时请求负 Q（吸收）。"""
        if dt_s <= 0 or q_min_kvar > q_max_kvar:
            raise ValueError("dt 必须为正且无功范围必须非空")
        if not valid or u_meas_pu is None:
            return AvcStep(0.0, 0.0, self.integral_kvar, False, False, "电压测量无效：冻结积分，不产生新无功请求")
        error = self.u_target_pu - u_meas_pu
        i_candidate = self.integral_kvar + self.ki_kvar_per_pu_s * error * dt_s
        q_raw = self.kp_kvar_per_pu * error + i_candidate
        q = clamp(q_raw, q_min_kvar, q_max_kvar)
        pushing_out = (q_raw < q_min_kvar and error < 0) or (q_raw > q_max_kvar and error > 0)
        if not pushing_out:
            self.integral_kvar = i_candidate
        return AvcStep(q, error, self.integral_kvar, pushing_out, True,
                       "无功能力顶住，冻结积分" if pushing_out else "电压 PI 请求")


# ================================================================ P-Q 圆投影
@dataclass
class PQProjection:
    p_kw: float
    q_kvar: float
    p_unserved_kw: float  # 请求 − 执行（带方向）
    q_unserved_kvar: float
    mode: str
    limited: bool
    reasons: list[str] = field(default_factory=list)


MODES = ("p_priority", "q_priority", "proportional")


def project_pq(
    p_req_kw: float,
    q_req_kvar: float,
    s_max_kva: float,
    mode: str = "p_priority",
    p_charge_max_kw: float | None = None,
    p_discharge_max_kw: float | None = None,
    q_max_kvar: float | None = None,
) -> PQProjection:
    """把 (P, Q) 请求投影进 P-Q 能力域（圆 ∩ 充放/无功上限），并报告未满足量。

    - p_priority：先保 P，Q 用剩余容量 √(S² − P²)；
    - q_priority：先保 Q，P 用剩余容量 √(S² − Q²)；
    - proportional：P、Q 按同一比例缩小（沿原点方向投影到圆上），保持功率因数不变。
    先做一维上限（充/放、无功上限），再做圆约束；圆约束不能用两次一维 clamp 代替。
    """
    if s_max_kva < 0:
        raise ValueError("视在容量必须非负")
    if mode not in MODES:
        raise ValueError(f"mode 只能是 {MODES}")
    if any(v is not None and v < 0 for v in (p_charge_max_kw, p_discharge_max_kw, q_max_kvar)):
        raise ValueError("上限必须是非负幅值")
    s = s_max_kva
    reasons: list[str] = []
    p_lo = -s if p_charge_max_kw is None else -min(s, p_charge_max_kw)
    p_hi = s if p_discharge_max_kw is None else min(s, p_discharge_max_kw)
    q_lim = s if q_max_kvar is None else min(s, q_max_kvar)
    p = clamp(p_req_kw, p_lo, p_hi)
    q = clamp(q_req_kvar, -q_lim, q_lim)
    if p != p_req_kw:
        reasons.append("有功超出充/放上限")
    if q != q_req_kvar:
        reasons.append("无功超出无功上限")

    if math.hypot(p, q) > s * (1 + 1e-12):
        if mode == "p_priority":
            q_cap = math.sqrt(max(0.0, s * s - p * p))
            q = math.copysign(min(abs(q), q_cap), q)
            reasons.append("有功优先：视在容量不足，压缩无功")
        elif mode == "q_priority":
            p_cap = math.sqrt(max(0.0, s * s - q * q))
            p = math.copysign(min(abs(p), p_cap), p)
            reasons.append("无功优先：视在容量不足，压缩有功")
        else:
            k = s / math.hypot(p, q)
            p, q = p * k, q * k
            reasons.append(f"按比例缩放 ×{k:.3f}：视在容量不足")
    return PQProjection(p, q, p_req_kw - p, q_req_kvar - q, mode, bool(reasons), reasons)


def naive_clamp_each(p_req_kw: float, q_req_kvar: float, s_max_kva: float) -> tuple[float, float]:
    """反例：把 P、Q 各自 clamp 到 ±S。结果可能落在圆外（超视在容量）。仅用于演示。"""
    return clamp(p_req_kw, -s_max_kva, s_max_kva), clamp(q_req_kvar, -s_max_kva, s_max_kva)

