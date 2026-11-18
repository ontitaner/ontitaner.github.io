# @AI_GENERATED
"""第 04 章配图：SOC/SOP 约束下的可行调度域。

参数对齐章节 04.2/04.3：[教学示例]
- E_nom=100 MWh, SOC 10%~90%（可用 80 MWh）, P_nom=50 MW, dt=1 h
- 放电上限 min(50, 可放能量×0.95/dt)，充电上限 min(50, 可充能量/0.95/dt)
"""
from __future__ import annotations

import numpy as np

from _style import C_DIS, C_CHG, C_SOC, C_TARGET, save, note, plt

E_NOM = 100.0
SOC_MIN, SOC_MAX = 0.10, 0.90
P_MAX = 50.0


def fig_feasible():
    soc = np.linspace(0.0, 1.0, 201)
    e_discharge = np.maximum(0.0, (soc - SOC_MIN) * E_NOM)
    e_charge = np.maximum(0.0, (SOC_MAX - soc) * E_NOM)
    p_dis = np.minimum(P_MAX, e_discharge * 0.95 / 1.0)
    p_chg = np.minimum(P_MAX, e_charge / 0.95 / 1.0)

    fig, ax = plt.subplots(figsize=(10.0, 5.0))
    ax.plot(soc, p_dis, color=C_DIS, lw=2.6, label="放电上限 P_dis_max")
    ax.plot(soc, -p_chg, color=C_CHG, lw=2.6, label="充电上限 −P_chg_max")
    ax.fill_between(soc, -p_chg, p_dis, color=C_SOC, alpha=0.08)
    ax.axhline(0, color="black", lw=0.8)
    ax.axvline(SOC_MIN, color=C_TARGET, ls="--", lw=1.2)
    ax.axvline(SOC_MAX, color=C_TARGET, ls="--", lw=1.2)
    ax.text(SOC_MIN + 0.01, 52, f"SOC_min={SOC_MIN:.0%}", color=C_TARGET, fontsize=9)
    ax.text(SOC_MAX - 0.05, 52, f"SOC_max={SOC_MAX:.0%}", color=C_TARGET, fontsize=9)

    note(ax, "SOC=50%：放 38 MW\n充 42.1 MW", (0.50, 38.0), (0.62, 42))
    note(ax, "SOC=90%：放满 50 MW\n充 0 MW", (0.90, 50.0), (0.70, 56))
    note(ax, "SOC=10%：放 0 MW\n充满 50 MW", (0.10, -50.0), (0.30, -56))

    ax.set_xlabel("SOC")
    ax.set_ylabel("功率上限 (MW)")
    ax.set_xlim(0, 1)
    ax.set_ylim(-60, 60)
    ax.legend(loc="upper center", fontsize=8.5)
    ax.set_title("可行调度域：SOC 决定的充/放电功率上限  [教学示例]")
    save(fig, "ch04_feasible")


def main():
    fig_feasible()
    print("  ch04: 1 figure saved")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end