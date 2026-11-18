# @AI_GENERATED
"""第 09 章配图：收益偏差归因瀑布图。

参数对齐章节 09.3：[教学示例]
- 计划利润 61726 → 电价误差 −11800 → 可用能量不足 −3400 → 实际利润 46526
"""
from __future__ import annotations

from _style import C_PROFIT, C_COST, C_ACC, save, note, plt


def fig_attribution():
    labels = ["计划利润", "电价误差", "可用能量\n不足", "实际利润"]
    steps = [
        (61726.0, C_PROFIT, 0.0, +1),
        (-11800.0, C_COST, 61726.0, -1),
        (-3400.0, C_COST, 61726.0 - 11800.0, -1),
    ]

    fig, ax = plt.subplots(figsize=(8.6, 4.8))
    for i, (val, color, bottom, _sign) in enumerate(steps):
        ax.bar(i, val, bottom=bottom, color=color, width=0.5, alpha=0.9)
        va = "center"
        ax.text(i, bottom + val / 2, f"{val:+,.0f}", ha="center", va=va,
                fontsize=11, fontweight="bold", color="white")

    final = 46526.0
    ax.bar(3, final, bottom=0, color=C_ACC, width=0.5, alpha=0.9)
    ax.text(3, final / 2, f"{final:,.0f}", ha="center", va="center",
            fontsize=11, fontweight="bold")

    note(ax, "计划 61726 元", (0, 61726), (0.8, 52000))
    note(ax, "实际 46526 元\n偏差 −15200", (3, 46526), (1.6, 38000))

    ax.set_xticks(range(4))
    ax.set_xticklabels(labels)
    ax.set_ylabel("利润 (元)")
    ax.set_ylim(0, 70000)
    ax.set_title("收益复盘：计划 vs 实际的偏差归因  [教学示例]")
    save(fig, "ch09_attribution")


def main():
    fig_attribution()
    print("  ch09: 1 figure saved")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end