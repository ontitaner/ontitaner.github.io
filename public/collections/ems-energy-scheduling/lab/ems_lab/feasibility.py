# @AI_GENERATED
"""SOC/SOP 约束下的可行调度域

对应章节：04 可行调度域

约定（附录B）：放电为正，SOC 0~1，能量 MWh，功率 MW。
"""
from __future__ import annotations

E_NOM = 100.0
SOC_MIN = 0.10
SOC_MAX = 0.90


def available_energy(soc: float, e_nom: float = E_NOM,
                     soc_min: float = SOC_MIN, soc_max: float = SOC_MAX) -> tuple:
    """返回 (可放能量, 可充能量) MWh（均为非负幅值）。"""
    e_discharge = (soc - soc_min) * e_nom
    e_charge = (soc_max - soc) * e_nom
    return e_discharge, e_charge


def feasible_p(soc: float, dt_h: float, p_max: float = 50.0, e_nom: float = E_NOM,
               soc_min: float = SOC_MIN, soc_max: float = SOC_MAX,
               eta_chg: float = 0.95, eta_dis: float = 0.95) -> tuple:
    """返回 (p_dis_max, p_chg_max) MW：本时段 dt_h 内可行的放电/充电功率上限。

    放电上限受 SOC 下限（可放能量×效率/时长）与额定功率双重约束；
    充电上限受 SOC 上限（可充能量/效率/时长）与额定功率双重约束。
    """
    e_discharge, e_charge = available_energy(soc, e_nom, soc_min, soc_max)
    p_dis_max = min(p_max, e_discharge * eta_dis / dt_h)
    p_chg_max = min(p_max, e_charge / eta_chg / dt_h)
    return p_dis_max, p_chg_max
# @AI_GENERATED: end