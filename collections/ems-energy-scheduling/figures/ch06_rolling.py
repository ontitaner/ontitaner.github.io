# @AI_GENERATED
"""第 06 章配图：日内滚动修正（固定计划 vs 理想重排）。

参数对齐章节 06.2：[教学示例]
- 三个时段价 [谷 350, A(平) 700→1300, B(峰) 1200]
- 固定计划（谷充→B 放）收益 61726 元；理想重排（谷充→A 放）收益 69326 元；改善 7600 元
"""
from __future__ import annotations

from _style import C_PROFIT, C_ACC, C_GRID, save, note, plt


def fig_rolling():
    labels = ["固定计划\n谷充→峰放", "理想重排\n谷充→平放", "改善"]
    values = [61726.0, 69326.0, 7600.0]
    colors = [C_GRID, C_PROFIT, C_ACC]

    fig, ax = plt.subplots(figsize=(7.8, 4.8))
    bars = ax.bar(labels, values, color=colors, width=0.55, alpha=0.9)
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 900, f"{val:,.0f} 元",
                ha="center", fontsize=11, fontweight="bold")

    note(ax, "平段意外涨到 1300\n超过峰段 1200", (1, 69326), (0.4, 58000))
    note(ax, "滚动重排多赚\n7600 元", (2, 7600), (1.4, 22000))

    ax.set_ylabel("收益 (元)")
    ax.set_ylim(0, 76000)
    ax.set_title("日内滚动修正：平段涨价时重排放电时段  [教学示例]")
    save(fig, "ch06_rolling")


def main():
    fig_rolling()
    print("  ch06: 1 figure saved")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end