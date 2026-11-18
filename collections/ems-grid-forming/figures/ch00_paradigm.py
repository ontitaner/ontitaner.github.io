# @AI_GENERATED
"""第 00 章配图：跟网型 vs 构网型——动态（惯量）与稳态（P-f 下垂）两维特征对比。

参数对齐章节 00.1/00.2/00.6：[教学示例]
- 调差率 δ = 3%，额定功率 P_n = 50 MW，额定频率 f_n = 50 Hz
- 下垂斜率 k = P_n/(δ·f_n) = 50/(0.03×50) = 33.33 MW/Hz
- 跟网型（无惯量）：RoCoF = (50.00-49.40)/0.8 = 0.75 Hz/s → 0.8s 触及低周保护阈值 49.40 Hz
- 构网型（虚拟惯量 J，系统惯量×3）：RoCoF = 0.75/3 = 0.25 Hz/s → 仅跌至 49.80 Hz
- 左图：频率-时间（动态特征）；右图：有功-频率（稳态下垂特征，死区 ±0.06 Hz）
"""
from __future__ import annotations

from _style import (C_DB, C_GFM, C_GFL, C_TRIP, plt, save)


def fig_paradigm():
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.3))

    # ---------- 左：频率-时间（动态特征：惯量支撑） ----------
    ax = axes[0]
    t_gfl = [0.0, 0.4, 0.8, 1.2, 1.6, 2.0]
    f_gfl = [50.00, 49.70, 49.40, 49.00, 48.60, 48.20]  # 0.8s 触及阈值后脱网扩大
    t_gfm = [0.0, 0.4, 0.8, 1.2, 1.6, 2.0]
    f_gfm = [50.00, 49.90, 49.80, 49.78, 49.80, 49.86]  # 一次调频后回升

    ax.plot(t_gfl, f_gfl, "-o", color=C_GFL, lw=2, ms=4, label="跟网型（无惯量）")
    ax.plot(t_gfm, f_gfm, "-o", color=C_GFM, lw=2, ms=4, label="构网型（虚拟惯量 J）")

    ax.axhline(49.40, color=C_TRIP, ls="--", lw=1.2)
    ax.text(0.02, 49.43, "低周保护阈值 49.40 Hz", color=C_TRIP, fontsize=9)
    ax.axhspan(49.94, 50.06, color=C_DB, alpha=0.25)
    ax.text(0.5, 50.13, "一次调频死区 ±0.06 Hz", color=C_DB, fontsize=8.5, ha="center")

    ax.annotate("跟网型（无惯量）RoCoF=0.75 Hz/s\n0.8s 跌至 49.40 Hz → 脱网扩大",
                xy=(0.8, 49.40), xytext=(0.10, 48.28),
                fontsize=9, arrowprops=dict(arrowstyle="->", color=C_GFL))
    ax.annotate("构网型（虚拟惯量 J）RoCoF=0.25 Hz/s\n仅跌至 49.80 Hz，未触发保护",
                xy=(0.8, 49.80), xytext=(1.02, 49.50),
                fontsize=9, arrowprops=dict(arrowstyle="->", color=C_GFM))

    ax.set_xlabel("时间 t (s)")
    ax.set_ylabel("频率 f (Hz)")
    ax.set_xlim(-0.05, 2.05)
    ax.set_ylim(48.0, 50.25)
    ax.set_title("动态特征：惯量支撑减缓 RoCoF  [教学示例]")
    ax.legend(loc="lower right")

    # ---------- 右：有功-频率（稳态特征：P-f 下垂 / 死区） ----------
    ax2 = axes[1]
    k = 50.0 / (0.03 * 50.0)  # 下垂斜率 = 33.33 MW/Hz
    # 构网型：无死区连续下垂，过额定点 (50.0, 50.0)
    f_gfm2 = [49.40, 50.20]
    p_gfm2 = [50.0 - k * (49.40 - 50.0), 50.0 - k * (50.20 - 50.0)]  # [70, 43.33]
    # 跟网型：死区 ±0.06 Hz 内不响应，死区外按同一调差率下垂
    f_gfl2 = [49.40, 49.94, 50.06, 50.20]
    p_gfl2 = [50.0 + k * (49.94 - 49.40), 50.0, 50.0, 50.0 - k * (50.20 - 50.06)]  # [68, 50, 50, 45.33]

    ax2.plot(f_gfm2, p_gfm2, "-", color=C_GFM, lw=2.2, label="构网型（无死区连续下垂）")
    ax2.plot(f_gfl2, p_gfl2, "-o", color=C_GFL, lw=2.2, ms=4, label="跟网型（死区 + 下垂）")

    ax2.axvspan(49.94, 50.06, color=C_DB, alpha=0.25)
    ax2.text(50.0, 42.0, "死区 ±0.06 Hz", color=C_DB, fontsize=8.5, ha="center")
    ax2.axvline(50.0, color="#cccccc", ls=":", lw=1.0)

    ax2.annotate("49.4 Hz：构网型 70 MW\n跟网型 68 MW",
                 xy=(49.40, 70.0), xytext=(49.62, 66.0),
                 fontsize=9, arrowprops=dict(arrowstyle="->", color=C_GFM))

    ax2.set_xlabel("频率 f (Hz)")
    ax2.set_ylabel("有功 P (MW)")
    ax2.set_xlim(49.35, 50.25)
    ax2.set_ylim(40.0, 76.0)
    ax2.set_title("稳态特征：P-f 下垂（死区 vs 连续）  [教学示例]")
    ax2.legend(loc="upper center", bbox_to_anchor=(0.5, -0.14), ncol=2, fontsize=8.5)

    save(fig, "ch00_paradigm")


def main():
    fig_paradigm()
    print("  ch00: 1 figure saved")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end