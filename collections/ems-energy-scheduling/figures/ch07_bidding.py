# @AI_GENERATED
"""第 07 章配图：现货报价决策（报价 vs 成本 vs 预测 LMP）。

参数对齐章节 07.3：[教学示例]
- 放电成本 450 元/MWh，预测 LMP 600 元/MWh，margin 10%
- 报价 = max(成本, 预测价 × 1.1) = 660 元/MWh
"""
from __future__ import annotations

import numpy as np

from _style import C_COST, C_ACC, C_DIS, C_GRID, save, note, plt


def fig_bidding():
    lmp = np.linspace(0, 900, 200)
    cost = 450.0
    margin = 0.10
    bid = np.maximum(cost, lmp * (1 + margin))

    fig, ax = plt.subplots(figsize=(9.5, 4.8))
    ax.plot(lmp, bid, color=C_ACC, lw=2.6, label="报价 = max(成本, 预测价×1.1)")
    ax.plot(lmp, lmp, color=C_GRID, lw=1.4, ls=":", label="报价 = 预测价（零毛利）")
    ax.axhline(cost, color=C_COST, ls="--", lw=1.6, label=f"放电成本 {cost:.0f} 元/MWh")

    ax.plot(600, 660, "o", color=C_DIS, ms=10, zorder=5)
    note(ax, "预测 LMP 600 → 报价 660\nmargin 10%", (600, 660), (640, 520))

    ax.set_xlabel("预测节点电价 LMP (元/MWh)")
    ax.set_ylabel("报价 (元/MWh)")
    ax.set_xlim(0, 900)
    ax.set_ylim(0, 1000)
    ax.legend(fontsize=8.5, loc="upper left")
    ax.set_title("现货报价：成本保底 + 预测价加成  [教学示例]")
    save(fig, "ch07_bidding")


def main():
    fig_bidding()
    print("  ch07: 1 figure saved")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end