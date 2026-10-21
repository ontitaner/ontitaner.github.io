"""第 15 章：单区域电网频率响应的教学模型（标幺值，系统容量为基准）。

    2H · dx/dt = ΔP_gov + ΔP_bess + ΔP_agc − ΔP_trip − D·x      x = Δf / fn

- 惯量：H 越大，同样的功率缺口下频率跌得越慢；
- 负荷阻尼 D：频率低时部分负荷（电动机）自然少用电；
- 一次调频（火电/水电调速器）：一阶惯性，时间常数 T_g，秒到十几秒；
- 二次调频（AGC）：积分作用，分钟级把频率拉回额定值；
- 储能：死区 + 下垂（可选虚拟惯量），响应时间常数 T_b 很小。

这是聚合的低阶模型，只用于理解各层调节的作用和时间尺度，不代表任何具体电网的实际参数。
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .control import deadband_shift


@dataclass
class GridParams:
    h_s: float = 4.0  # 系统惯性时间常数 [教学示例]
    d_pu: float = 1.0  # 负荷阻尼系数 [教学示例]
    gov_gain: float = 10.0  # 等效调速器增益 = 参与比例 / 调差率 [教学示例]
    gov_tau_s: float = 6.0  # 调速器+汽轮机等效时间常数 [教学示例]
    gov_headroom_pu: float = 0.05  # 机组可增出力上限
    agc_ki: float = 0.0  # AGC 积分增益，0 表示不投 AGC
    agc_rate_pu_s: float = 0.0004  # AGC 出力变化率上限（每秒）
    agc_delay_s: float = 30.0  # AGC 开始动作的时间
    f_nominal_hz: float = 50.0


@dataclass
class BessParams:
    rating_pu: float = 0.0  # 储能容量占系统容量比例，0 表示没有储能
    droop_ratio: float = 0.01  # 调差率 δ
    deadband_hz: float = 0.03
    limit_ratio: float = 1.0  # 调频出力上限，占储能额定功率比例
    tau_s: float = 0.2  # 储能响应等效时间常数（含测量、通信、PCS）
    h_virtual_s: float = 0.0  # 虚拟惯量时间常数，0 表示不投


@dataclass
class SimResult:
    t: np.ndarray
    f_hz: np.ndarray
    p_gov: np.ndarray
    p_bess: np.ndarray
    p_agc: np.ndarray
    p_inertia: np.ndarray  # 转子动能释放 = −2H·dx/dt
    p_damping: np.ndarray
    extras: dict = field(default_factory=dict)

    @property
    def nadir_hz(self) -> float:
        return float(self.f_hz.min())

    @property
    def nadir_time_s(self) -> float:
        return float(self.t[int(self.f_hz.argmin())])


def simulate_trip(
    trip_pu: float,
    grid: GridParams,
    bess: BessParams,
    t_end_s: float = 30.0,
    dt: float = 0.01,
    t_trip_s: float = 1.0,
) -> SimResult:
    if grid.h_s <= 0:
        raise ValueError("惯性时间常数必须为正")
    if dt <= 0:
        raise ValueError("仿真步长必须为正")
    if t_end_s < 0:
        raise ValueError("仿真结束时间不能为负")
    if bess.rating_pu < 0:
        raise ValueError("储能容量比例不能为负")
    if bess.rating_pu > 0 and bess.tau_s <= 0:
        raise ValueError("储能响应时间常数必须为正")
    n = int(round(t_end_s / dt)) + 1
    t = np.arange(n) * dt
    x = 0.0
    p_gov = p_bess = p_agc = 0.0
    x_prev = 0.0
    out = {k: np.zeros(n) for k in ("f", "gov", "bess", "agc", "inertia", "damp")}
    for k in range(n):
        dp_trip = trip_pu if t[k] >= t_trip_s else 0.0

        # 储能：死区 + 下垂 + 可选虚拟惯量，经一阶惯性执行
        if bess.rating_pu > 0:
            dfx_hz = deadband_shift(x * grid.f_nominal_hz, bess.deadband_hz)
            p_droop = -(dfx_hz / grid.f_nominal_hz) / bess.droop_ratio  # 占储能额定的比例
            rocof_pu = (x - x_prev) / dt
            p_vi = -2.0 * bess.h_virtual_s * rocof_pu
            cmd_ratio = np.clip(p_droop + p_vi, -bess.limit_ratio, bess.limit_ratio)
            p_bess += (cmd_ratio * bess.rating_pu - p_bess) / bess.tau_s * dt

        # 调速器（一次调频）
        gov_target = min(-grid.gov_gain * x, grid.gov_headroom_pu)
        p_gov += (gov_target - p_gov) / grid.gov_tau_s * dt

        # AGC（二次调频）：积分，限速
        if grid.agc_ki > 0 and t[k] >= t_trip_s + grid.agc_delay_s:
            step = float(np.clip(-grid.agc_ki * x * dt, -grid.agc_rate_pu_s * dt, grid.agc_rate_pu_s * dt))
            p_agc += step

        p_damp = -grid.d_pu * x
        imbalance = p_gov + p_bess + p_agc - dp_trip + p_damp
        x_prev = x
        x += imbalance / (2.0 * grid.h_s) * dt

        out["f"][k] = grid.f_nominal_hz * (1 + x)
        out["gov"][k] = p_gov
        out["bess"][k] = p_bess
        out["agc"][k] = p_agc
        out["damp"][k] = p_damp
        out["inertia"][k] = -imbalance  # 缺口由转子动能补：正值表示动能在释放
    return SimResult(t, out["f"], out["gov"], out["bess"], out["agc"], out["inertia"], out["damp"])

