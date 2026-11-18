# @AI_GENERATED
"""第 02 章配图：两种死区对比、完整下垂特性曲线。

所有参数均为 [教学示例]，不可直接用于现场整定。
"""
from __future__ import annotations

import numpy as np

from _style import (C_CHG, C_DIS, C_GRID, C_LIMIT, C_OK, C_ACC, C_PURPLE, C_WIND, C_SOLAR,
                    IMG_DIR, manifest, save, deadband_shift, deadband_cut, plt)

FN = 50.0  # 额定频率


def fig_deadband_compare():
    """两种死区的出力对比（连续型 vs 截断型）"""
    pn = 100  # MW
    delta_pct = 3.0  # %
    deadband_hz = 0.06
    limit_pct = 10.0
    k = pn / (delta_pct / 100 * FN)  # MW/Hz

    f = np.linspace(49.70, 50.30, 1001)
    df = f - FN

    eff_cont = deadband_shift(df, deadband_hz)
    eff_cut = deadband_cut(df, deadband_hz)
    dp_cont = np.clip(-k * eff_cont, -limit_pct / 100 * pn, limit_pct / 100 * pn)
    dp_cut = np.clip(-k * eff_cut, -limit_pct / 100 * pn, limit_pct / 100 * pn)

    fig, axes = plt.subplots(1, 2, figsize=(11, 5), sharey=True)

    for ax, dp, title, color in [
        (axes[0], dp_cont, "连续型（平移）死区", C_OK),
        (axes[1], dp_cut, "截断型（削平）死区", C_ACC),
    ]:
        ax.plot(f, dp, color=color, lw=2.5)
        ax.axvspan(FN - deadband_hz, FN + deadband_hz, color=C_GRID, alpha=0.12)
        ax.axvline(FN - deadband_hz, color=C_LIMIT, ls="--", lw=1, alpha=0.6)
        ax.axvline(FN + deadband_hz, color=C_LIMIT, ls="--", lw=1, alpha=0.6)
        ax.axhline(0, color="k", lw=0.8)
        ax.axhline(limit_pct / 100 * pn, color=C_LIMIT, ls=":", lw=1)
        ax.axhline(-limit_pct / 100 * pn, color=C_LIMIT, ls=":", lw=1)
        ax.set_xlabel("电网频率 (Hz)")
        ax.set_title(title, fontsize=11)
        ax.set_xlim(49.72, 50.28)

        # 标注工作点
        if title.startswith("连续"):
            f_pt, dp_pt = 49.90, dp_cont[np.argmin(np.abs(f - 49.90))]
            ax.plot(f_pt, dp_pt, "o", color=C_DIS, ms=8, zorder=5)
            ax.annotate(f"f={f_pt} Hz\nΔP={dp_pt:.1f} MW", xy=(f_pt, dp_pt),
                        xytext=(49.78, dp_pt - 1.5),
                        arrowprops=dict(arrowstyle="->", color=C_DIS), fontsize=9)
            ax.text(49.76, 4.5, "死区边界处\n出力从 0 连续增长", fontsize=8.5,
                    bbox=dict(fc="white", ec=C_GRID, alpha=0.85))
        else:
            f_pt, dp_pt = 49.90, dp_cut[np.argmin(np.abs(f - 49.90))]
            ax.plot(f_pt, dp_pt, "o", color=C_DIS, ms=8, zorder=5)
            ax.annotate(f"f={f_pt} Hz\nΔP={dp_pt:.1f} MW", xy=(f_pt, dp_pt),
                        xytext=(49.78, dp_pt - 1.5),
                        arrowprops=dict(arrowstyle="->", color=C_DIS), fontsize=9)
            jump_p = k * deadband_hz
            ax.annotate(f"边界处跳变\n{deadband_hz*1000:.0f} mHz×K={jump_p:.1f} MW",
                        xy=(FN + deadband_hz + 0.002, jump_p),
                        xytext=(50.12, jump_p + 2),
                        arrowprops=dict(arrowstyle="->", color=C_LIMIT),
                        fontsize=8.5, color=C_LIMIT)

    axes[0].set_ylabel("一次调频出力增量 ΔP (MW)")
    fig.suptitle(f"死区 ±{int(deadband_hz*1000)} mHz 的实际出力差异  [Pn={pn} MW, δ={delta_pct}%, 限幅 ±{limit_pct}% Pn]",
                 fontsize=11, y=1.01)
    fig.text(0.51, -0.04, "阴影区 = 死区  |  水平虚线 = 限幅 ±10 MW  |  [教学示例参数]",
             ha="center", fontsize=8.5, color=C_GRID)

    manifest("ch02_deadband_compare",
             [pn, delta_pct, deadband_hz * 1000, limit_pct, FN, 49.90, dp_pt, jump_p, -jump_p])
    save(fig, "ch02_deadband_compare")


def fig_droop_full():
    """完整下垂特性：死区、调差率 K 线、限幅、方向"""
    pn = 100  # MW
    delta_pct = 3.0
    deadband_hz = 0.06
    limit_pct = 10.0
    k = pn / (delta_pct / 100 * FN)

    f = np.linspace(49.50, 50.50, 2001)
    df = f - FN
    eff = deadband_shift(df, deadband_hz)
    dp_raw = -k * eff
    dp = np.clip(dp_raw, -limit_pct / 100 * pn, limit_pct / 100 * pn)

    fig, ax = plt.subplots(figsize=(9, 5.5))

    # 斜率参考虚线（超出限幅前）
    mask_slope = (np.abs(dp_raw) < limit_pct / 100 * pn) & (np.abs(df) > deadband_hz)
    f_slope = f[mask_slope]
    dp_slope = dp[mask_slope]

    ax.plot(f, dp, color=C_OK, lw=2.8, label="实际下垂特性（含限幅）")
    ax.plot(f, dp_raw, color=C_GRID, lw=1, ls="--", alpha=0.5, label="理论下垂（不限幅）")

    # 死区
    ax.axvspan(FN - deadband_hz, FN + deadband_hz, color=C_ACC, alpha=0.12, label=f"死区 ±{int(deadband_hz*1000)} mHz")
    ax.axvline(FN - deadband_hz, color=C_LIMIT, ls="--", lw=1.2)
    ax.axvline(FN + deadband_hz, color=C_LIMIT, ls="--", lw=1.2)
    ax.text(FN - deadband_hz - 0.015, 11.5, f"{FN-deadband_hz:.2f}", fontsize=8, color=C_LIMIT, ha="right")
    ax.text(FN + deadband_hz + 0.005, 11.5, f"{FN+deadband_hz:.2f}", fontsize=8, color=C_LIMIT)

    # 限幅线
    limit_val = limit_pct / 100 * pn
    ax.axhline(limit_val, color=C_LIMIT, ls="--", lw=1.2)
    ax.axhline(-limit_val, color=C_LIMIT, ls="--", lw=1.2)
    ax.text(50.35, limit_val + 0.3, f"限幅 +{int(limit_val)} MW\n(+{int(limit_pct)}% Pn)",
            fontsize=8.5, color=C_LIMIT)
    ax.text(49.55, -limit_val - 1.3, f"限幅 −{int(limit_val)} MW\n(−{int(limit_pct)}% Pn)",
            fontsize=8.5, color=C_LIMIT)

    # 达到限幅的频点
    f_reach_limit_low = FN - deadband_hz - limit_val / k
    f_reach_limit_high = FN + deadband_hz + limit_val / k
    for f_lim, y_lim, ha in [(f_reach_limit_low, limit_val, "left"),
                               (f_reach_limit_high, -limit_val, "right")]:
        ax.plot(f_lim, y_lim, "s", color=C_PURPLE, ms=7, zorder=5)
    ax.annotate(f"达到限幅\n{f_reach_limit_low:.2f} Hz", xy=(f_reach_limit_low, limit_val),
                xytext=(f_reach_limit_low + 0.06, limit_val - 3),
                arrowprops=dict(arrowstyle="->", color=C_PURPLE),
                fontsize=8.5, color=C_PURPLE)
    ax.annotate(f"达到限幅\n{f_reach_limit_high:.2f} Hz", xy=(f_reach_limit_high, -limit_val),
                xytext=(f_reach_limit_high - 0.06, -limit_val + 3),
                arrowprops=dict(arrowstyle="->", color=C_PURPLE),
                fontsize=8.5, color=C_PURPLE, ha="right")

    # 调差率说明框
    ax.annotate(f"调差率 δ={delta_pct}%\nK = Pn/(δ×fn)\n  = {pn}/({delta_pct/100}×50)\n  = {k:.1f} MW/Hz\n\n含义：频率每偏 0.1 Hz\n出力变化 {k*0.1:.1f} MW",
                xy=(0.02, 0.96), xycoords="axes fraction", ha="left", va="top",
                fontsize=8.5,
                bbox=dict(fc="white", ec=C_GRID, alpha=0.9, boxstyle="round"))

    # 方向标注
    ax.fill_between([FN + deadband_hz, 50.5], 0, 12, color=C_CHG, alpha=0.06)
    ax.fill_between([49.5, FN - deadband_hz], -12, 0, color=C_DIS, alpha=0.06)
    ax.text(50.18, 7, "频率高 → 充电（ΔP<0）", color=C_CHG, fontsize=9, ha="center")
    ax.text(49.82, -7, "频率低 → 放电（ΔP>0）", color=C_DIS, fontsize=9, ha="center")

    # 工作点示例
    for f_pt, c in [(49.90, C_DIS), (50.10, C_CHG)]:
        idx = np.argmin(np.abs(f - f_pt))
        ax.plot(f_pt, dp[idx], "o", color=c, ms=9, zorder=5)
    ax.annotate(f"49.90 Hz\nΔP={dp[np.argmin(np.abs(f-49.90))]:.1f} MW",
                xy=(49.90, dp[np.argmin(np.abs(f-49.90))]),
                xytext=(49.72, dp[np.argmin(np.abs(f-49.90))] + 2.5),
                arrowprops=dict(arrowstyle="->", color=C_DIS), fontsize=9, color=C_DIS)

    ax.set_xlabel("电网频率 (Hz)")
    ax.set_ylabel("一次调频出力增量 ΔP (MW)")
    ax.set_title(f"四个参数：死区{int(deadband_hz*1000)} mHz | δ={delta_pct}% | 限幅 ±{int(limit_val)} MW | 方向：ΔP=−K×Δf  [教学示例]")
    ax.set_xlim(49.55, 50.45)
    ax.set_ylim(-13, 13)
    ax.axhline(0, color="k", lw=0.8)
    ax.axvline(FN, color="k", lw=0.5, alpha=0.3)
    ax.legend(loc="lower right", fontsize=8)

    manifest("ch02_droop_full",
             [pn, delta_pct, deadband_hz * 1000, limit_val, FN, k, 49.90, 49.79, 50.21])
    save(fig, "ch02_droop_full")


def main():
    fig_deadband_compare()
    fig_droop_full()


if __name__ == "__main__":
    main()
# @AI_GENERATED: end