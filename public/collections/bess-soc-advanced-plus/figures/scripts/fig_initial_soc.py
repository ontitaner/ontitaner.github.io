# @AI_GENERATED
"""图：初始 SOC 获取 — 三种路径对比 + EKF 收敛 + 不确定度演化。"""
from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt

from _figstyle import C_CHG, C_DIS, C_GRID, C_OK, IMG_DIR, plt, save

def main():
    np.random.seed(42)
    fig = plt.figure(figsize=(14, 13))
    gs = fig.add_gridspec(3, 1, hspace=0.30, height_ratios=[1, 1, 1])
    ax1 = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1])
    ax3 = fig.add_subplot(gs[2])
    fig.suptitle("初始 SOC 获取：三种路径对比 → EKF 收敛轨迹 → 不确定度演化",
                 fontsize=13, y=0.98)

    # ── 场景参数 ──
    soc_true = 47.0
    soc_eeprom = 46.98
    soc_voltage = 48.5
    off_hours = 2.25
    total_h = 3.0
    dt = 2.0
    tau_converge = 0.6 * 3600  # EKF 收敛时间常数

    t = np.arange(0, total_h * 3600, dt)
    t_h = t / 3600.0

    # 断电段标记
    ax1.axvspan(0, off_hours, color=C_GRID, alpha=0.08)
    ax1.axvspan(off_hours, total_h, color=C_OK, alpha=0.04)

    # ── 上栏：三种初值 ──
    ax1.axhline(y=soc_true, color="black", lw=1.0, ls="--", alpha=0.5, label="真实 SOC=47.0%")
    ax1.plot(off_hours, soc_eeprom, "o", color=C_CHG, ms=12, markeredgewidth=2,
             markeredgecolor="darkblue", label=f"路径A EEPROM {soc_eeprom}%", zorder=10)
    ax1.plot(off_hours, soc_voltage, "s", color=C_DIS, ms=12, markeredgewidth=2,
             markeredgecolor="darkred", label=f"路径B 电压反查 {soc_voltage}%", zorder=10)
    ax1.plot(off_hours, soc_true, "D", color=C_GRID, ms=10, markeredgewidth=2,
             markeredgecolor="black", label=f"路径C 满充重置 (不可用)", zorder=9)

    ax1.annotate("断电 2.25 h", xy=(off_hours / 2, soc_true + 0.4),
                 fontsize=10, ha="center", color=C_GRID,
                 bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=C_GRID, alpha=0.85))
    ax1.annotate("BMS 上电", xy=(off_hours + 0.02, soc_true + 0.8),
                 fontsize=10, ha="left", color=C_GRID,
                 arrowprops=dict(arrowstyle="->", color=C_GRID, lw=1.2))

    ax1.set_ylabel("SOC (%)")
    ax1.set_title("上栏：断电后 BMS 上电 — 三种路径给出的 SOC 初值", fontsize=11)
    ax1.legend(loc="lower left", fontsize=9, framealpha=0.9)
    ax1.set_ylim(45.5, 50.5)

    # ── 中栏：EKF 收敛轨迹 ──
    def ekf_trajectory(soc_start, p0, label, color, ls="-"):
        traj = np.zeros_like(t_h)
        for i, th in enumerate(t_h):
            if th < off_hours:
                traj[i] = np.nan
            else:
                elapsed = (th - off_hours) * 3600
                e = soc_start - soc_true
                traj[i] = soc_start - e * (1 - np.exp(-elapsed / tau_converge))
        ax2.plot(t_h, traj, color=color, lw=2.0, ls=ls, label=label, alpha=0.9)
        return traj

    ekf_trajectory(soc_eeprom, 0.0001, "路径A EEPROM → EKF 几乎无修正", C_CHG)
    ekf_trajectory(soc_voltage, 0.01, "路径B 电压反查 → EKF 收敛 ~0.7 h", C_DIS)

    ax2.axhline(y=soc_true, color="black", lw=1.0, ls="--", alpha=0.5)
    ax2.axvline(x=off_hours + tau_converge / 3600, color=C_DIS, lw=0.8, ls=":",
                alpha=0.5)
    ax2.annotate("收敛约 0.7 h", xy=(off_hours + 0.7, soc_true - 0.3),
                 fontsize=9.5, color=C_DIS, ha="center")
    ax2.set_ylabel("SOC (%)")
    ax2.set_title("中栏：EKF 收敛轨迹 — 初值偏差越大、可观测性越弱，收敛越慢", fontsize=11)
    ax2.legend(loc="lower left", fontsize=9, framealpha=0.9)
    ax2.set_ylim(45.5, 50.5)

    # ── 下栏：不确定度 ±2σ ──
    sigma_eeprom = 0.05
    sigma_voltage = 1.5

    def uncertainty_band(center, sigma, color, alpha_fill=0.15):
        upper = center + 2 * sigma
        lower = center - 2 * sigma
        ax3.fill_between(t_h, lower, upper, color=color, alpha=alpha_fill, lw=0)
        ax3.plot(t_h, center, color=color, lw=1.5, alpha=0.9)

    # EEPROM 路径
    center_a, sigma_a = np.ones_like(t_h) * soc_eeprom, np.ones_like(t_h) * sigma_eeprom
    center_a[t_h < off_hours] = np.nan
    upper_a = center_a + 2 * sigma_a
    lower_a = center_a - 2 * sigma_a
    ax3.fill_between(t_h, lower_a, upper_a, color=C_CHG, alpha=0.15, lw=0)
    ax3.plot(t_h, center_a, color=C_CHG, lw=1.8, label="路径A EEPROM ±2σ")

    # 电压反查路径：不确定度随时间衰减
    sigma_v = sigma_voltage * np.exp(-(np.maximum(t_h - off_hours, 0) * 3600) / tau_converge)
    center_v = soc_voltage - (soc_voltage - soc_true) * (1 - np.exp(-np.maximum(t_h - off_hours, 0) * 3600 / tau_converge))
    center_v[t_h < off_hours] = np.nan
    sigma_v[t_h < off_hours] = np.nan
    ax3.fill_between(t_h, center_v - 2 * sigma_v, center_v + 2 * sigma_v,
                     color=C_DIS, alpha=0.12, lw=0)
    ax3.plot(t_h, center_v, color=C_DIS, lw=1.8, ls="--", label="路径B 电压反查 ±2σ")

    ax3.axhline(y=soc_true, color="black", lw=1.0, ls="--", alpha=0.5)
    ax3.set_xlabel("时间 (h)")
    ax3.set_ylabel("SOC (%)")
    ax3.set_title("下栏：不确定度 ±2σ 区间 — EEPROM 始终紧窄，电压反查从宽收窄", fontsize=11)
    ax3.legend(loc="lower left", fontsize=9, framealpha=0.9)
    ax3.set_ylim(41, 53)

    save(fig, "initial_soc")

if __name__ == "__main__":
    main()