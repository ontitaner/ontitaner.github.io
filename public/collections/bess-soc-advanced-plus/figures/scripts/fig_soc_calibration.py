# @AI_GENERATED
"""图：SOC 校准与重置 — 满充校准 vs 开环漂移，展示校准对零漂的切断效应。"""
from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt

from _figstyle import C_CHG, C_DIS, C_GRID, C_OK, C_LIMIT, IMG_DIR, plt, save

def main():
    np.random.seed(42)
    fig = plt.figure(figsize=(14, 13))
    gs = fig.add_gridspec(3, 1, hspace=0.28, height_ratios=[0.8, 1.2, 1.0])
    ax1 = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1])
    ax3 = fig.add_subplot(gs[2])
    fig.suptitle("SOC 校准与重置：满充校准对开环漂移的切断效应",
                 fontsize=13, y=0.98)

    total_h = 48
    dt = 60.0
    t = np.arange(0, total_h * 3600, dt)
    t_h = t / 3600.0
    n = len(t)

    # 模拟电池运行：充放循环 + 满充事件
    current = np.zeros(n)
    voltage = np.zeros(n)
    soc_true = np.zeros(n)
    soc_ah_uncorrected = np.zeros(n)
    soc_ah_calibrated = np.zeros(n)

    q_nom = 280.0
    b_i = 0.5
    soc = 40.0
    soc_unc = 40.0
    soc_cal = 40.0
    eta = 0.998

    for i in range(n):
        if i == 0:
            soc_true[i] = soc
            soc_ah_uncorrected[i] = soc
            soc_ah_calibrated[i] = soc
            continue

        th = t_h[i]
        # 日模式：0-6h 静置, 6-12h 充电(80A), 12-15h 静置, 15-20h 放电(-100A), 20-24h 静置
        hour_in_day = th % 24
        if 6 <= hour_in_day < 12:
            i_cur = 80.0
        elif 15 <= hour_in_day < 20:
            i_cur = -100.0
        else:
            i_cur = 0.0

        current[i] = i_cur

        dsoc_true = (i_cur * eta) * dt / 3600.0 / q_nom * 100
        soc = (soc + dsoc_true) if i_cur != 0 else soc - 0.1 / 100 * dt / 3600.0
        soc_true[i] = np.clip(soc, 0, 100)

        soc_unc = soc_unc + (i_cur * eta + b_i) * dt / 3600.0 / q_nom * 100
        soc_ah_uncorrected[i] = soc_unc

        soc_cal = soc_cal + (i_cur * eta + b_i) * dt / 3600.0 / q_nom * 100
        soc_ah_calibrated[i] = soc_cal

        # 模拟电压
        if i_cur > 0:
            voltage[i] = 3.30 + soc_true[i] * (3.65 - 3.30) / 100 + i_cur * 0.00032
        elif i_cur < 0:
            voltage[i] = 3.30 + soc_true[i] * (3.65 - 3.30) / 100 + i_cur * 0.00032
        else:
            voltage[i] = 3.30 + soc_true[i] * (3.65 - 3.30) / 100

    # 模拟两次满充事件
    for fc_time, fc_soc in [(12.25, 18.0), (36.25, 42.0)]:
        idx = int(fc_time * 3600 / dt)
        if idx < n:
            soc_ah_calibrated[idx:] += (100.0 - soc_ah_calibrated[idx])

    # ── 上栏：电压 ──
    ax1.plot(t_h, voltage, color=C_GRID, lw=0.8)
    ax1.axhline(y=3.65, color=C_LIMIT, lw=1.0, ls="--", alpha=0.7)
    ax1.set_ylabel("电压 (V)")
    ax1.set_title("上栏：电池电压 + 满充截止线 3.65 V", fontsize=11)
    ax1.annotate("满充截止 3.65 V", xy=(36, 3.655), fontsize=9, color=C_LIMIT, ha="center")

    for fc_time, label in [(12.25, "满充 #1\nSOC→100%"), (36.25, "满充 #2\nSOC→100%")]:
        ax1.axvline(x=fc_time, color=C_OK, lw=2.0, ls="-", alpha=0.8)
        ax1.annotate(label, xy=(fc_time, 3.48), fontsize=9.5, color=C_OK, ha="center",
                     fontweight="bold",
                     bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=C_OK, alpha=0.85))

    # ── 中栏：三条 SOC 轨迹 ──
    ax2.plot(t_h, soc_true, color="black", lw=2.0, label="真实 SOC")
    ax2.plot(t_h, soc_ah_uncorrected, color=C_DIS, lw=2.0, ls="--",
             label="无校准安时积分（零漂持续累积）")
    ax2.plot(t_h, soc_ah_calibrated, color=C_OK, lw=2.2, ls="-.",
             label="有校准安时积分（满充后重置）")

    for fc_time in [12.25, 36.25]:
        ax2.axvline(x=fc_time, color=C_OK, lw=1.5, ls=":", alpha=0.6)

    ax2.set_ylabel("SOC (%)")
    ax2.set_title("中栏：SOC 轨迹对比 — 校准将偏差归零", fontsize=11)
    ax2.legend(loc="upper left", fontsize=9, framealpha=0.9)

    # ── 下栏：偏差 ──
    bias_unc = soc_ah_uncorrected - soc_true
    bias_cal = soc_ah_calibrated - soc_true
    ax3.fill_between(t_h, 0, bias_unc, color=C_DIS, alpha=0.12, lw=0)
    ax3.plot(t_h, bias_unc, color=C_DIS, lw=2.0, ls="--",
             label="无校准偏差（不受控制地累积）")
    ax3.plot(t_h, bias_cal, color=C_OK, lw=2.2, ls="-",
             label="有校准偏差（每次满充归零）")

    for fc_time in [12.25, 36.25]:
        ax3.axvline(x=fc_time, color=C_OK, lw=1.5, ls=":", alpha=0.6)
    ax3.axhline(y=0, color="black", lw=0.8, ls="-", alpha=0.5)

    ax3.set_xlabel("时间 (h)")
    ax3.set_ylabel("SOC 偏差 (百分点)")
    ax3.set_title("下栏：SOC 偏差 — 校准是零漂的剪刀，每次切断累积线", fontsize=11)
    ax3.legend(loc="upper left", fontsize=9, framealpha=0.9)

    save(fig, "soc_calibration")

if __name__ == "__main__":
    main()