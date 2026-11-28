# @AI_GENERATED
"""第 03 章核心模块：辐照 -> 光伏出力转换。

约定（对齐 02.x / 03.x 手算、附录B）：
- 测量平面链路：气象站 GHI -> 组件平面 POA -> 组件直流 P_module -> 逆变交流 P_ac -> 并网点 P_pv。
- 跨平面换算（附录B B.3）：P_pv = P_module × η − P_limit − P_maint（效率乘法、限电/检修减法）。
- 温度修正：P_module = P_rated × (POA/G_ref) × [1 + γ(T_cell − T_ref)]，γ < 0 表示高温降额。
- 电池温度（NOCT 线性模型）：T_cell = T_amb + (NOCT − 20)·POA/NOCT_IRR。
- 逆变削峰（饱和）：直流 ×η 后超过逆变器额定 P_inv_rated 时，输出被削到 P_inv_rated。

教学示例默认值（对齐 03.x 手算，主线 30 MWp 光伏）：
- P_rated = 30 MWp、G_ref = 1000 W/m²、η = 0.95（附录B）
- γ = -0.35%/°C（=-0.0035）、T_ref = 25 °C、NOCT = 45 °C、NOCT_IRR = 800 W/m²
- 逆变器额定 P_inv_rated = 25 MW（教学示例，用于演示削峰/饱和）
- 手算主案例：G = 800 W/m²、T_amb = 20 °C -> T_cell = 45 °C -> 降额 7%
  -> P_module = 30×0.8×0.93 = 22.32 MW -> P_ac = 22.32×0.95 = 21.204 MW
- 削峰案例：G = 1000 W/m²、STC（T_cell = 25 °C）-> P_module = 30 MW -> 30×0.95 = 28.5 MW -> 削到 25 MW
"""
from __future__ import annotations

G_REF = 1000.0      # 标况辐照 W/m²
GAMMA = -0.0035     # 功率温度系数 /°C（-0.35%/°C）
T_REF = 25.0        # STC 电池温度 °C
NOCT = 45.0         # 额定电池工作温度 °C
NOCT_IRR = 800.0    # NOCT 对应辐照 W/m²


def ghi_to_poa(ghi: float, transposition: float = 1.0) -> float:
    """GHI（水平面辐照）-> POA（组件平面辐照）。

    转置系数 K_t 由倾角/朝向/直散分离决定；教学示例取 1.0（对齐 02 章 GHI=POA 简化）。
    """
    if ghi < 0:
        raise ValueError(f"辐照不能为负，实际 {ghi}")
    return ghi * transposition


def cell_temperature(t_amb: float, poa: float, noct: float = NOCT,
                     noct_irr: float = NOCT_IRR) -> float:
    """环境温度 -> 电池温度（NOCT 线性模型）：T_cell = T_amb + (NOCT − 20)·POA/NOCT_IRR。

    辐照越强电池越热：POA = 800 W/m² 时电池比环境高 NOCT−20 = 25 °C。
    """
    if noct_irr <= 0:
        raise ValueError(f"NOCT 辐照必须为正，实际 {noct_irr}")
    return t_amb + (noct - 20.0) * poa / noct_irr


def temperature_factor(t_cell: float, gamma: float = GAMMA, t_ref: float = T_REF) -> float:
    """温度降额系数 = 1 + γ(T_cell − T_ref)。

    γ < 0：高温（T_cell > T_ref）时系数 < 1，即降额；低温时 > 1（增益）。
    """
    return 1.0 + gamma * (t_cell - t_ref)


def pv_dc_power(p_rated: float, poa: float, t_cell: float, g_ref: float = G_REF,
                gamma: float = GAMMA, t_ref: float = T_REF) -> float:
    """POA + 温度 -> 组件直流出力（MW）：P_module = P_rated·(POA/G_ref)·[1+γ(T_cell−T_ref)]。

    STC（POA=G_ref、T_cell=T_ref）时退化为 P_rated × POA/G_ref（02 章理想线性）。
    """
    if p_rated < 0:
        raise ValueError(f"额定功率不能为负，实际 {p_rated}")
    if poa < 0:
        raise ValueError(f"辐照不能为负，实际 {poa}")
    if g_ref <= 0:
        raise ValueError(f"标况辐照必须为正，实际 {g_ref}")
    return p_rated * (poa / g_ref) * temperature_factor(t_cell, gamma, t_ref)


def inverter_ac(dc_mw: float, eta: float = 0.95, inv_rating: float | None = None) -> float:
    """直流 -> 交流（MW）：×η 后按逆变器额定削峰（饱和）。

    inv_rating=None 表示不削峰；否则 ac = min(dc×η, inv_rating)。
    """
    if dc_mw < 0:
        raise ValueError(f"直流功率不能为负，实际 {dc_mw}")
    if not 0.0 < eta <= 1.0:
        raise ValueError(f"效率必须在 (0,1]，实际 {eta}")
    ac = dc_mw * eta
    if inv_rating is not None and ac > inv_rating:
        return inv_rating
    return ac


def pv_pcc_power(ac_mw: float, limit_mw: float = 0.0, maint_mw: float = 0.0) -> float:
    """交流 -> 并网点光伏上网出力：P_pv = ac − limit − maint（限电/检修为减法，下界 0）。

    对齐附录B B.3 的跨平面换算（P_pv = P_module × η − P_limit − P_maint 的末段减项）。
    """
    out = ac_mw - limit_mw - maint_mw
    return out if out > 0.0 else 0.0
# @AI_GENERATED: end