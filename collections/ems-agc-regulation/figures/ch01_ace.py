# @AI_GENERATED
"""第 01 章配图：ACE = ΔP_tie + B × Δf 的分解 + 三种控制模式对比。

全篇唯一业务事件：邻省 600 MW 机组跳闸（ΔP_tie=+50、Δf=−0.10）。
所有参数均为 [教学示例]（B = 1000 MW/Hz），不可直接用于现场整定。
数据与正文 01 章「ACE 的物理含义」「三种控制模式」手算逐字一致。
"""
from __future__ import annotations

import numpy as np

from _style import (C_GRID, C_LIMIT, C_ACC, C_OK, C_TBC, C_FFC, C_FTC,
                    C_K1, manifest, save, plt)

B = 1000.0  # MW/Hz（教学示例）

# 全篇唯一业务事件：邻省 600 MW 机组跳闸
DP_TIE = 50.0   # ΔP_tie = +50 MW（本区被迫多送，送出为正）
DF = -0.10      # Δf = -0.10 Hz（频率 49.90 Hz）


def _bf(df: float) -> float:
    return B * df


def _ace(dp: float, df: float) -> float:
    return dp + B * df


def fig_ace_decomposition():
    """单一业务事件（邻省 600 MW 机组跳闸）的 ACE 分量分解。"""
    dp = DP_TIE
    df = DF
    bf = _bf(df)             # -100
    ace_val = _ace(dp, df)   # -50

    labels = ["ΔP_tie\n联络线偏差", "B×Δf\n频率偏差项", "ACE\n合成"]
    vals = [dp, bf, ace_val]
    colors = [C_GRID, C_ACC, C_K1]

    fig, ax = plt.subplots(figsize=(7.5, 5.2))
    x = np.arange(len(labels))
    bars = ax.bar(x, vals, 0.5, color=colors, alpha=0.92)
    ax.axhline(0, color=C_GRID, lw=1.2)

    for xi, v in zip(x, vals):
        c = C_K1 if xi == 2 else (C_GRID if xi == 0 else C_ACC)
        ax.text(xi, v + (3 if v >= 0 else -3), f"{v:+.0f}", ha="center",
                va="bottom" if v >= 0 else "top", fontsize=10, color=c,
                fontweight="bold")

    # 合成柱加粗边框，突出"ACE"这一根
    bars[2].set_edgecolor(C_K1)
    bars[2].set_linewidth(2.4)

    # 关键标注：两项异号，频率项主导
    ax.annotate("ΔP_tie=+50（被迫多送）\nB×Δf=−100（缺电更严重）\n→ ACE=−50 仍要增出力",
                xy=(2.0, -50.0), xytext=(1.2, -108),
                arrowprops=dict(arrowstyle="->", color=C_K1),
                fontsize=8.5, color=C_K1,
                bbox=dict(fc="white", ec=C_K1, alpha=0.95))

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_ylabel("功率偏差 (MW)")
    ax.set_ylim(-125, 80)
    ax.set_title("ACE = ΔP_tie + B×Δf 的分解（邻省 600 MW 机组跳闸，B=1000 MW/Hz）",
                 fontsize=11)
    ax.text(0.5, -0.16, "ACE < 0 → 需增出力；ACE > 0 → 需减出力",
            transform=ax.transAxes, ha="center", fontsize=8.5, color=C_GRID)

    manifest("ch01_ace_decomposition", vals + [df, B])
    save(fig, "ch01_ace_decomposition")


def fig_mode_compare():
    """唯一业务事件（邻省 600 MW 机组跳闸）下三种模式的控制量对比，FTC 方向错误。"""
    labels = ["FFC\n只看频率", "FTC\n只看联络线", "TBC\n频率+联络线"]
    vals = [-100.0, 50.0, -50.0]
    colors = [C_FFC, C_FTC, C_TBC]

    fig, ax = plt.subplots(figsize=(7.5, 5.0))
    x = np.arange(len(labels))
    bars = ax.bar(x, vals, 0.55, color=colors, alpha=0.92)
    ax.axhline(0, color=C_GRID, lw=1.2)

    for xi, v, lbl in zip(x, vals, labels):
        ax.text(xi, v + (3 if v >= 0 else -3), f"{v:.0f} MW", ha="center",
                va="bottom" if v >= 0 else "top", fontsize=10, fontweight="bold")
        tag = "增出力" if v < 0 else "减出力"
        ax.text(xi, 70, tag, ha="center", fontsize=9,
                color=C_OK if v < 0 else C_LIMIT, fontweight="bold")

    # FTC 方向错误高亮
    ax.annotate("FTC 只看联络线\n给出「减出力」——方向错误！\n区外跳闸本区该增出力支援",
                xy=(1.0, 50.0), xytext=(0.45, 88),
                arrowprops=dict(arrowstyle="->", color=C_LIMIT),
                fontsize=8.5, color=C_LIMIT,
                bbox=dict(fc="white", ec=C_LIMIT, alpha=0.95))
    bars[1].set_edgecolor(C_LIMIT)
    bars[1].set_linewidth(2.4)

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_ylabel("控制量 (MW)")
    ax.set_ylim(-125, 125)
    ax.set_yticks([-100, -50, 0, 50, 100])
    ax.set_title("同一事件（邻省 600 MW 机组跳闸）三种模式的控制量对比", fontsize=11)
    ax.text(0.5, -0.12, "事件：邻省 600 MW 机组跳闸，ΔP_tie=+50 MW、Δf=−0.10 Hz、B=1000 MW/Hz",
            transform=ax.transAxes, ha="center", fontsize=8.5, color=C_GRID)

    manifest("ch01_mode_compare", vals + [B, 50.0, -0.10])
    save(fig, "ch01_mode_compare")


def main():
    print("[ch01_ace]")
    fig_ace_decomposition()
    fig_mode_compare()


if __name__ == "__main__":
    main()