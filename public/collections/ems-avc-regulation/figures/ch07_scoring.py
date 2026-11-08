# @AI_GENERATED
"""第 07 章配图：AVC 月度考核评分瀑布图 + 子项构成。

参数对齐章节 07.1~07.3：[教学示例]
- 评分：电压 94.6%→78.6, 投运率 97.5%→90.0, 调节性能 55.0
- 权重 50/30/20，综合 77.3 (<80 → 系数 0.85)
"""
from __future__ import annotations

import numpy as np

from _style import (C_OK, C_ACC, C_Q_ABSORB, C_TARGET, C_LIMIT,
                    C_VOLTAGE,
                    IMG_DIR, save, note, plt)


def fig_scoring_waterfall():
    w_v, w_a, w_q = 0.50, 0.30, 0.20
    steps = [
        ("满分 100", 100.0, C_OK),
        ("电压合格 −10.7\n94.6%×50%", -10.7, C_VOLTAGE),
        ("投运率 −3.0\n97.5%×30%", -3.0, C_Q_ABSORB),
        ("调节性能 −9.0\n55.0×20%", -9.0, C_LIMIT),
    ]

    fig, ax = plt.subplots(figsize=(8.5, 5))
    level = 0.0
    xs = np.arange(len(steps) + 1)
    for i, (label, value, color) in enumerate(steps):
        bottom = level if value >= 0 else level + value
        ax.bar(i, abs(value), bottom=bottom, color=color, alpha=0.85, width=0.55)
        sign = "+" if value >= 0 else ""
        ax.text(i, bottom + abs(value) * 2 - 5 if value < 0 else bottom + abs(value) / 2,
                f"{sign}{value:.1f}", ha="center", fontsize=10, fontweight="bold",
                color="white" if abs(value) > 5 else "black")
        new_level = level + value
        ax.plot([i + 0.275, i + 0.725], [new_level, new_level], color=C_TARGET, lw=1)
        level = new_level
    final = 77.3
    ax.bar(len(steps), final, color=C_LIMIT, alpha=0.9, width=0.55)
    ax.text(len(steps), final + 1.5, f"= {final:.1f}", ha="center", fontsize=11, fontweight="bold")
    ax.axhline(80, color=C_OK, ls="--", lw=2, label="及格线 80 分")
    note(ax, f"<80 → 考核系数 0.85\n基准 ¥10000×0.85=¥8500\n少拿 ¥1500/月", (3, final),
         (1.5, final + 15))
    ax.set_xticks(xs, [s[0] for s in steps] + ["综合 77.3"])
    ax.set_ylabel("得分")
    ax.set_ylim(0, 110)
    ax.set_title("AVC 月度评分瀑布图  [电压 94.6%/投运 97.5%/响应 28s, 华东权重 50/30/20]", fontsize=10)
    ax.legend(fontsize=8.5)
    ax.grid(axis="x", visible=False)
    save(fig, "ch07_scoring_waterfall")


def fig_sub_scores():
    sub_items = ["电压合格率", "AVC 投运率", "无功调节性能"]
    sub_raw = [78.6, 90.0, 55.0]
    sub_w = [78.6 * 0.50, 90.0 * 0.30, 55.0 * 0.20]
    colors = [C_VOLTAGE, C_Q_ABSORB, C_LIMIT]

    fig, ax = plt.subplots(figsize=(8, 4.5))
    x = np.arange(3)
    w = 0.35
    ax.bar(x - w / 2, sub_raw, w, color=colors, alpha=0.3, label="原始得分", edgecolor="white")
    ax.bar(x + w / 2, sub_w, w, color=colors, alpha=0.85, label="加权后 (50%/30%/20%)", edgecolor="white")
    for i, (r, wv) in enumerate(zip(sub_raw, sub_w)):
        ax.text(i - w / 2, r + 1, f"{r:.0f}", ha="center", fontsize=9, color=C_TARGET)
        ax.text(i + w / 2, wv + 1, f"{wv:.1f}", ha="center", fontsize=11, fontweight="bold")
    ax.set_xticks(x, sub_items)
    ax.set_title("子项得分构成：权重放大电压影响", fontsize=10)
    ax.legend(fontsize=8.5)
    ax.set_ylim(0, 100)
    save(fig, "ch07_sub_scores")


def main():
    fig_scoring_waterfall()
    fig_sub_scores()
    print(f"  ch07: 2 figures saved")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end