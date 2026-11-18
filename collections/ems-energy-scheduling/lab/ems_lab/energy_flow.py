# @AI_GENERATED
"""能量流换算与 SOC 递推

对应章节：01 峰谷套利（效率），04 可行调度域（SOC 递推）

约定（附录B）：放电为正（P>0 放电），SOC 0~1。
"""
from __future__ import annotations

ETA_CHG = 0.95
ETA_DIS = 0.95
E_NOM = 100.0   # MWh
SOC_MIN = 0.10
SOC_MAX = 0.90


def stored_from_grid(e_grid_mwh: float, eta_chg: float = ETA_CHG) -> float:
    """充电：从电网吸收 e_grid（MWh），电池存入的能量（MWh）。"""
    return e_grid_mwh * eta_chg


def out_from_stored(e_stored_mwh: float, eta_dis: float = ETA_DIS) -> float:
    """放电：电池放出 e_stored（MWh），并网输出的能量（MWh）。"""
    return e_stored_mwh * eta_dis


def step_soc(soc: float, p_mw: float, dt_h: float, e_nom: float = E_NOM,
             eta_chg: float = ETA_CHG, eta_dis: float = ETA_DIS) -> float:
    """单步 SOC 递推。p_mw>0 放电、p_mw<0 充电，返回 clamp 到 [0,1] 的新 SOC。"""
    if p_mw >= 0:
        delta = -p_mw * dt_h / eta_dis / e_nom
    else:
        delta = -p_mw * eta_chg * dt_h / e_nom
    return min(1.0, max(0.0, soc + delta))
# @AI_GENERATED: end