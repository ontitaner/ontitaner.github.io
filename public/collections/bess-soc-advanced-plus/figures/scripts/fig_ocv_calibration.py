# @AI_GENERATED
"""图：OCV-SOC 曲线构建 — GITT 标定全过程三栏分解。"""
from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt

from _figstyle import C_CHG, C_DIS, C_GRID, IMG_DIR, plt, save

def main():
    np.random.seed(42)
    fig = plt.figure(figsize=(12, 13))
    gs = fig.add_gridspec(3, 1, hspace=0.32, height_ratios=[0.9, 1.2, 1.1])
    ax1 = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1])
    ax3 = fig.add_subplot(gs[2])
    fig.suptitle("GITT 标定：分段充放电测试 → 端电压静置衰减 → OCV-SOC 曲线构建",
                 fontsize=13, y=0.98)

    steps = 21
    charge_current = 15.7
    discharge_current = -15.7
    rest_dur = 2 * 3600
    step_dur = 720
    period = step_dur + rest_dur
    dt = 2.0
    tau = 20.0
    r0 = 0.32e-3

    total = 2 * steps * period
    n = int(total / dt)
    time = np.arange(0, total, dt)
    current = np.zeros(n)
    voltage = np.zeros(n)
    ocv_charge, ocv_discharge = [], []

    OCV_CHG = np.array([2.500, 2.620, 2.780, 2.950, 3.120, 3.170,
                        3.200, 3.225, 3.248, 3.265, 3.280, 3.292,
                        3.300, 3.310, 3.318, 3.327, 3.340, 3.360,
                        3.393, 3.440, 3.500])
    OCV_DIS = np.array([2.500, 2.616, 2.772, 2.942, 3.114, 3.164,
                        3.194, 3.219, 3.242, 3.259, 3.274, 3.286,
                        3.294, 3.304, 3.312, 3.321, 3.334, 3.356,
                        3.389, 3.438, 3.500])

    dstep = int(step_dur / dt)
    dperiod = int(period / dt)

    def fill_step(offset_k, cur_val, ocv_arr, rev):
        for k in range(steps):
            i0 = offset_k + k * dperiod
            i_end_chg = i0 + dstep
            i_end_rest = i0 + dperiod
            if i_end_rest > n:
                break
            current[i0:i_end_chg] = cur_val
            ir0 = cur_val * r0
            ocv_k = ocv_arr[steps - 1 - k] if rev else ocv_arr[k]
            voltage[i0:i_end_chg] = ocv_k + ir0
            for j in range(i_end_chg, i_end_rest):
                voltage[j] = ocv_k + ir0 * np.exp(-(j - i_end_chg) * dt / tau)
            (ocv_discharge if rev else ocv_charge).append(ocv_k)

    fill_step(0, charge_current, OCV_CHG, rev=False)
    fill_step(steps * dperiod, discharge_current, OCV_DIS, rev=True)

    time_h = time / 3600.0

    # ── 上栏：电流 ──
    ax1.fill_between(time_h, 0, current, color=C_CHG, alpha=0.30, step="mid")
    ax1.plot(time_h, current, color=C_CHG, lw=1.0, drawstyle="steps-mid")
    ax1.axhline(y=0, color=C_GRID, lw=0.5)
    ax1.set_ylabel("电流 (A)", color=C_CHG)
    ax1.tick_params(axis="y", labelcolor=C_CHG)
    ax1.set_title("上栏：电流激励（C/20 ≈ 15.7 A 分段充放 + 每步静置 2 h）", fontsize=11)

    mid_h = steps * period / 3600
    ax1.annotate("充电阶段", xy=(mid_h * 0.35, 17), fontsize=10, color=C_CHG, fontweight="bold")
    ax1.annotate("放电阶段", xy=(mid_h * 1.4, -17), fontsize=10, color=C_DIS, fontweight="bold")

    # ── 中栏：端电压 ──
    ax2.plot(time_h, voltage, color=C_GRID, lw=0.6)
    ax2.set_ylabel("端电压 (V)")
    ax2.set_title("中栏：端电压响应 — 每步充放后静置衰减，静置终点 = OCV 点", fontsize=11)
    for si in [5, 10, 15]:
        t0 = (si * period + step_dur) / 3600.0
        ax2.axvspan(t0, t0 + rest_dur / 3600.0, color=C_DIS, alpha=0.06)
    ax2.annotate("静置段\n(2 h)", xy=(4.5, 2.56), fontsize=8.5, color=C_DIS, ha="center")
    ax2.annotate("静置终点\n→ OCV 点",
                 xy=(6.8, 3.30), fontsize=9.5, color=C_GRID, ha="center",
                 bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=C_GRID, alpha=0.8))

    # ── 下栏：OCV-SOC ──
    soc_arr = np.linspace(0, 1, len(ocv_charge))
    ax3.plot(soc_arr, ocv_charge, "o", color=C_CHG, ms=5, alpha=0.7, label="充电方向 OCV")
    ax3.plot(soc_arr, ocv_discharge, "s", color=C_DIS, ms=5, alpha=0.7, label="放电方向 OCV")
    ocv_mean = (np.array(ocv_charge) + np.array(ocv_discharge)) / 2
    ax3.plot(soc_arr, ocv_mean, "k-", lw=2.5, label="OCV 均值（最终标定曲线）", zorder=10)
    ax3.set_xlabel("SOC")
    ax3.set_ylabel("OCV (V)")
    ax3.set_title("下栏：充放方向 OCV 提取 → 取均值消除滞回 → 最终 OCV-SOC 曲线", fontsize=11)
    ax3.annotate("平台区\n(斜率 ≈ 0.02–0.06 V/SOC)\n信息量弱",
                 xy=(0.50, 3.300), fontsize=9.5, ha="center", va="top",
                 bbox=dict(boxstyle="round,pad=0.4", fc="lightyellow", ec=C_GRID, alpha=0.85))
    ax3.annotate("陡坡区\n(斜率 > 0.2 V/SOC)\n信息量强",
                 xy=(0.06, 2.88), fontsize=9, ha="center",
                 bbox=dict(boxstyle="round,pad=0.35", fc="lavender", ec=C_GRID, alpha=0.85))
    ax3.annotate("陡坡区\n信息量强",
                 xy=(0.94, 3.48), fontsize=9, ha="center",
                 bbox=dict(boxstyle="round,pad=0.35", fc="lavender", ec=C_GRID, alpha=0.85))
    ax3.legend(loc="lower right", fontsize=9.5, framealpha=0.9)
    ax3.axvspan(0.30, 0.80, color=C_GRID, alpha=0.05)

    save(fig, "ocv_calibration")

if __name__ == "__main__":
    main()