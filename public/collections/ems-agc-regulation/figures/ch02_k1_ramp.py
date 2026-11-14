# @AI_GENERATED
"""第 02 章配图：K1 调节速率多级限速瓶颈（三级取最小）+ 逐层修复后的瓶颈上移。

全篇唯一业务对象：华东某 100 MW / 200 MWh 储能电站（4 台 25 MW PCS）。
全篇唯一业务事件：邻省 600 MW 机组跳闸后省调下发 AGC「上调 50 MW」。
所有参数均为 [教学示例]，不可直接用于现场整定。

数据与正文 02 章「参数一：调节速率 K1」手算逐字一致：
  调度要求 K1 = 1.0 Pn/min = 1.67 MW/s（留 20% 余量则三层均需 ≥ 2.0 MW/s）
  现场当前配置：PCS 硬件 0.8 / EMS 安全限速 1.0 / 分配模块合成 1.2（MW/s）
  三级取最小值：min(0.8, 1.0, 1.2) = 0.8 MW/s = 0.48 Pn/min → 卡在 PCS 硬件
"""
from __future__ import annotations

import numpy as np

from _style import (C_K1, C_ACC, C_OK, C_LIMIT, C_GRID,
                    manifest, save, plt)

PN = 100.0                   # MW
K1_PN_PER_MIN = 1.0          # Pn/min（调度要求）
K1_MW_PER_S = K1_PN_PER_MIN * PN / 60  # 1.67 MW/s
MARGIN = 1.2                 # 20% 安全余量
TARGET = K1_MW_PER_S * MARGIN  # 2.0 MW/s（三层均需抬到此值）

PCS = 0.8     # MW/s（4 台 × 0.2）
EMS = 1.0     # MW/s
ALLOC = 1.2   # MW/s


def fig_k1_bottleneck():
    """三级限速取最小值：三条横向条取最短，虚线为调度要求。"""
    labels = ["PCS 硬件\n(4 台 × 0.2)", "EMS 安全限速", "分配模块合成"]
    vals = [PCS, EMS, ALLOC]
    colors = [C_K1, C_ACC, C_OK]

    fig, ax = plt.subplots(figsize=(8.6, 5.4))
    y = np.arange(len(labels))[::-1]
    bars = ax.barh(y, vals, 0.52, color=colors, alpha=0.92)

    # 调度要求 + 安全余量两条竖向参考线
    ax.axvline(K1_MW_PER_S, color=C_LIMIT, ls="--", lw=2.0,
               label=f"调度要求 K1 = 1.0 Pn/min = {K1_MW_PER_S:.2f} MW/s")
    ax.axvline(TARGET, color=C_OK, ls=":", lw=1.8,
               label=f"安全余量线 = {TARGET:.1f} MW/s")

    for yi, v in zip(y, vals):
        ax.text(v + 0.03, yi, f"{v:.1f} MW/s", va="center", ha="left",
                fontsize=11, fontweight="bold", color="black")

    # 最短条（PCS）加粗边框，突出瓶颈
    bars[0].set_edgecolor(C_LIMIT)
    bars[0].set_linewidth(2.6)

    ax.annotate("min(0.8, 1.0, 1.2) = 0.8 MW/s\n实际 K1 被卡在 PCS 硬件",
                xy=(PCS, y[0]), xytext=(1.02, y[0] + 0.52),
                arrowprops=dict(arrowstyle="->", color=C_LIMIT),
                fontsize=9, color=C_LIMIT,
                bbox=dict(fc="white", ec=C_LIMIT, alpha=0.95))

    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=10)
    ax.set_xlabel("限速值 (MW/s)", fontsize=11)
    ax.set_xlim(0, 2.7)
    ax.set_ylim(-0.65, 2.95)
    ax.set_xticks([0, 0.5, 1.0, 1.67, 2.0])
    ax.set_title("K1 三级限速取最小值：min(0.8, 1.0, 1.2) = 0.8 MW/s（卡 PCS 硬件）",
                 fontsize=12, pad=12)
    ax.legend(loc="lower right", fontsize=8, framealpha=0.9)
    ax.text(0.5, -0.14, "三条横条取最短，不是相加、也不是平均——最短那根就是实际 K1",
            transform=ax.transAxes, ha="center", fontsize=8.5, color=C_GRID)

    manifest("ch02_k1_bottleneck",
             vals + [K1_MW_PER_S, TARGET, 0.48, 0.2])
    save(fig, "ch02_k1_bottleneck")


def fig_k1_repair():
    """逐层修复后的瓶颈上移：当前→修PCS→修EMS→全修，四组取各自最短。"""
    groups = ["当前", "修 PCS", "修 EMS", "全修"]
    pcs_vals = [0.8, 2.0, 2.0, 2.0]
    ems_vals = [1.0, 1.0, 2.0, 2.0]
    alloc_vals = [1.2, 1.2, 1.2, 2.0]
    mins = [0.8, 1.0, 1.2, 2.0]
    min_labels = ["卡 PCS 硬件", "卡 EMS 限速", "卡分配合成", "达标"]

    fig, ax = plt.subplots(figsize=(10.5, 6.2))
    y = np.arange(len(groups))[::-1]
    h = 0.22

    b1 = ax.barh(y + h, pcs_vals, h, color=C_K1, label="PCS 硬件")
    b2 = ax.barh(y, ems_vals, h, color=C_ACC, label="EMS 安全限速")
    b3 = ax.barh(y - h, alloc_vals, h, color=C_OK, label="分配模块合成")

    # 调度要求 + 安全余量两条竖向参考线（顶部文字标注）
    ax.axvline(K1_MW_PER_S, color=C_LIMIT, ls="--", lw=2.0)
    ax.axvline(TARGET, color=C_OK, ls=":", lw=1.8)
    ax.text(K1_MW_PER_S, 3.34, f"调度要求 K1 = {K1_MW_PER_S:.2f} MW/s",
            ha="center", va="bottom", fontsize=8.5, color=C_LIMIT, fontweight="bold")
    ax.text(TARGET, 3.34, f"安全余量线 = {TARGET:.1f} MW/s",
            ha="center", va="bottom", fontsize=8.5, color=C_OK, fontweight="bold")

    # 每根条数值标注
    for bars in (b1, b2, b3):
        for r in bars:
            v = r.get_width()
            ax.text(v + 0.03, r.get_y() + r.get_height() / 2, f"{v:.1f}",
                    va="center", ha="left", fontsize=8, fontweight="bold")

    # 每组最短条加粗边框（全修组达标则全绿框）
    for i in range(len(groups)):
        if i < 3:
            jmin = int(np.argmin([pcs_vals[i], ems_vals[i], alloc_vals[i]]))
            [b1[i], b2[i], b3[i]][jmin].set_edgecolor(C_LIMIT)
            [b1[i], b2[i], b3[i]][jmin].set_linewidth(2.4)
        else:
            for b in (b1[i], b2[i], b3[i]):
                b.set_edgecolor(C_OK)
                b.set_linewidth(2.0)

    # 每组右侧标注该组的 min 结果
    for i in range(len(groups)):
        ok = i == 3
        c = C_OK if ok else C_LIMIT
        ax.text(2.42, y[i], f"min={mins[i]:.1f} MW/s", va="center", ha="left",
                fontsize=10, fontweight="bold", color=c)
        ax.text(2.42, y[i] - 0.34, min_labels[i], va="center", ha="left",
                fontsize=8, color=c)

    ax.set_yticks(y)
    ax.set_yticklabels(groups, fontsize=11)
    ax.set_xlabel("限速值 (MW/s)", fontsize=11)
    ax.set_xlim(0, 3.6)
    ax.set_ylim(-0.95, 3.5)
    ax.set_title("逐层修复后的瓶颈上移：最矮那层会动态换人", fontsize=12.5, pad=14)
    ax.legend(loc="lower left", ncol=3, fontsize=8, framealpha=0.9)

    ax.text(0.5, -0.17,
            "从上到下看每组最短条：PCS(0.8) → EMS(1.0) → 分配(1.2) → 全修(2.0 ≥ 1.67 达标)",
            transform=ax.transAxes, ha="center", fontsize=8.5, color=C_GRID)

    manifest("ch02_k1_repair",
             [0.8, 1.0, 1.2, 2.0, K1_MW_PER_S, TARGET])
    save(fig, "ch02_k1_repair")


def main():
    print("[ch02_k1_ramp]")
    fig_k1_bottleneck()
    fig_k1_repair()


if __name__ == "__main__":
    main()
# @AI_GENERATED: end