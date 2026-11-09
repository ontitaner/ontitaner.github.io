# @AI_GENERATED
"""第 01 章配图：分时电价 24h 柱状图 + 一充一放收益瀑布。

参数对齐章节 01.2/01.3：[教学示例]
- 谷 0.35 / 平 0.70 / 峰 1.20 元/kWh
- 一充一放：谷充 80MWh（电网吸收 84.21），峰放 76MWh（并网）
"""
from __future__ import annotations

import numpy as np

from _style import (C_CHG, C_DIS, C_GRID, C_PROFIT, C_COST, C_PRICE,
                    save, note, plt)

PRICES = [0.35] * 8 + [0.70] * 2 + [1.20] * 2 + [0.70] * 5 + [1.20] * 4 + [0.70] * 2 + [0.35]


def fig_price():
    hours = np.arange(24)
    prices = np.array(PRICES)
    colors = [C_CHG if p == 0.35 else (C_DIS if p == 1.20 else C_GRID) for p in prices]

    fig, ax = plt.subplots(figsize=(10.5, 4.4))
    ax.bar(hours, prices, color=colors, width=0.72)
    ax.set_xticks(hours)
    ax.set_xlabel("小时 (h)")
    ax.set_ylabel("电价 (元/kWh)")
    ax.set_ylim(0, 1.48)

    note(ax, "谷段 0.35 元/kWh\n23:00–08:00 共 9 h", (3.5, 0.35), (6.0, 1.05))
    note(ax, "峰段 1.20 元/kWh\n10–12、17–21 共 6 h", (11.5, 1.20), (14.5, 1.30))
    note(ax, "平段 0.70 元/kWh\n其余 9 h", (15.5, 0.70), (11.0, 0.52))

    ax.axhline(0.85, color=C_DIS, ls="--", lw=1.1)
    ax.text(0.2, 0.88, "峰谷价差 = 0.85 元/kWh", color=C_DIS, fontsize=9.5)
    ax.set_title("分时电价 24h：谷 0.35 / 平 0.70 / 峰 1.20 元/kWh  [教学示例]")
    save(fig, "ch01_price")


def fig_arbitrage():
    labels = ["放电收入", "充电成本", "净收益"]
    bars = [
        (91200.0, C_PROFIT, 0.0),
        (-29474.0, C_COST, 91200.0),
    ]

    fig, ax = plt.subplots(figsize=(7.6, 4.8))
    for i, (val, color, bottom) in enumerate(bars):
        ax.bar(i, val, bottom=bottom, color=color, width=0.52, alpha=0.9)
        ax.text(i, bottom + val / 2, f"{val:+,.0f} 元", ha="center", va="center",
                fontsize=10.5, fontweight="bold", color="white")
    # 合计柱
    total = 61726.0
    ax.bar(2, total, bottom=0, color=C_PRICE, width=0.52, alpha=0.9)
    ax.text(2, total / 2, f"{total:,.0f} 元", ha="center", va="center",
            fontsize=10.5, fontweight="bold")

    note(ax, "峰放 76 MWh\n76×1200", (0, 91200), (1.4, 76000))
    note(ax, "谷充 84.21 MWh\n80/0.95×350", (1, 91200 - 29474), (1.3, 55000))
    note(ax, "往返效率 0.90\n80→76 MWh", (2, 61726), (1.1, 30000))

    ax.set_xticks(range(3))
    ax.set_xticklabels(labels)
    ax.set_ylabel("金额 (元)")
    ax.set_ylim(0, 98000)
    ax.set_title("一充一放收益：谷充 80MWh → 峰放 76MWh  [教学示例]")
    save(fig, "ch01_arbitrage")


def main():
    fig_price()
    fig_arbitrage()
    print("  ch01: 2 figures saved")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end