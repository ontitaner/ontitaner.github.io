# @AI_GENERATED
"""第 03 章配图：多资源无功分配三种策略对比 + 联合 P-Q 可行域 + 电容离散过补。

参数对齐章节 03.2~03.5：[教学示例]
- Q_total=−8000 kvar, SVG ±15 Mvar, PCS×10 ±50 Mvar, 电容 −10 Mvar
- 联合 P-Q: 3×5000 kVA PCS 不同 P 水平
"""
from __future__ import annotations

import numpy as np

from _style import (C_OK, C_ACC, C_Q_ABSORB, C_Q_GENERATE, C_TARGET, C_LIMIT,
                    C_SVG, C_PCS, C_CAPACITOR,
                    IMG_DIR, save, note, plt)


def fig_multi_resource():
    q_total = -8000

    fig, axes = plt.subplots(1, 3, figsize=(12, 5), sharey=True)

    # 策略一：按剩余容量比例
    cap_rem = [15000, 30000, 10000]
    alloc_cap = [q_total * c / sum(cap_rem) for c in cap_rem]
    ax = axes[0]
    x = [0, 1, 2]
    bars = ax.bar(x, alloc_cap, color=[C_SVG, C_PCS, C_CAPACITOR], alpha=0.85, width=0.55)
    ax.axhline(0, color="black", lw=0.8)
    ax.axhline(q_total, color=C_TARGET, ls="--", lw=1.5, label=f"需求 Q={q_total}")
    for bar, val in zip(bars, alloc_cap):
        ax.text(bar.get_x() + bar.get_width() / 2, val - 400, f"{int(val)}",
                ha="center", fontsize=9, fontweight="bold", color="white")
    ax.set_xticks(x, ["SVG\n±15Mvar", "PCS×10\n±50Mvar", "电容\n−10Mvar"])
    ax.set_title("按剩余容量\nQ_i ∝ S_i_remain", fontsize=10)
    ax.legend(fontsize=8)

    # 策略二：按速度
    alloc_spd = [-8000, 0, 0]
    ax = axes[1]
    bars = ax.bar(x, alloc_spd, color=[C_SVG, C_PCS, C_CAPACITOR], alpha=0.85, width=0.55)
    ax.axhline(0, color="black", lw=0.8)
    ax.axhline(q_total, color=C_TARGET, ls="--", lw=1.5)
    for bar, val in zip(bars, alloc_spd):
        ax.text(bar.get_x() + bar.get_width() / 2, val - 400 if val != 0 else 100,
                f"{int(val)}", ha="center", fontsize=9, fontweight="bold",
                color="white" if val != 0 else "black")
    ax.set_xticks(x, ["SVG\n±15Mvar", "PCS×10\n±50Mvar", "电容\n−10Mvar"])
    ax.set_title("按响应速度\nSVG 优先吃饱", fontsize=10)
    note(ax, "SVG 抢跑\n吃满 −8000", (0, -8000), (1, -5000))

    # 策略三：按经济
    alloc_eco = [0, 0, -8000]
    ax = axes[2]
    bars = ax.bar(x, alloc_eco, color=[C_SVG, C_PCS, C_CAPACITOR], alpha=0.85, width=0.55)
    ax.axhline(0, color="black", lw=0.8)
    ax.axhline(q_total, color=C_TARGET, ls="--", lw=1.5)
    for bar, val in zip(bars, alloc_eco):
        ax.text(bar.get_x() + bar.get_width() / 2, val - 400 if val != 0 else 100,
                f"{int(val)}", ha="center", fontsize=9, fontweight="bold",
                color="white" if val != 0 else "black")
    ax.set_xticks(x, ["SVG\n±15Mvar", "PCS×10\n±50Mvar", "电容\n−10Mvar"])
    ax.set_title("按经济损耗\n电容最便宜", fontsize=10)
    note(ax, "电容离散挡位\n−8000 → 切 −10000\n过补 +2000 kvar!", (2, -8000), (1.2, -5000))

    axes[0].set_ylabel("Q (kvar)")
    for ax in axes:
        ax.set_ylim(-10000, 2000)

    fig.suptitle("多资源无功分配：三种策略各有取舍  [Q_total=−8000 kvar 教材示例]", fontsize=11)
    save(fig, "ch03_multi_resource")


def fig_pq_joint():
    pcs_s = [5000, 5000, 5000]
    scenarios = [([0, 0, 0], "P=0\n[0,0,0]"),
                 ([2000, 2500, 3000], "中P\n[2,2.5,3]MW"),
                 ([4000, 3500, 2000], "高P\n[4,3.5,2]MW"),
                 ([4500, 4500, 4000], "AGC满\n[4.5,4.5,4]MW")]
    q_vals = [sum(np.sqrt(max(0, s**2 - p**2)) for s, p in zip(pcs_s, pl)) for pl, _ in scenarios]
    colors = [C_OK, C_ACC, C_Q_ABSORB, C_LIMIT]

    fig, ax = plt.subplots(figsize=(7, 4.5))
    x = np.arange(len(scenarios))
    bars = ax.bar(x, [v / 1000 for v in q_vals], 0.55, color=colors, alpha=0.85)
    for i, (v, (_, label)) in enumerate(zip(q_vals, scenarios)):
        ax.text(i, v / 1000 + 0.3, f"{v/1000:.1f} Mvar", ha="center", fontsize=11, fontweight="bold")
    ax.set_xticks(x, [label for _, label in scenarios])
    ax.set_ylabel("联合可用 Q (Mvar)")
    ax.set_title("联合 P-Q 可行域：P 越高 Q 越少\n3×5000 kVA PCS", fontsize=10)
    note(ax, "AGC 满发时 Q 腰斩\n12.8 → 6.2 Mvar", (3, 6.2), (2.2, 13))
    ax.set_ylim(0, 17)
    save(fig, "ch03_pq_joint_domain")


def main():
    fig_multi_resource()
    fig_pq_joint()
    print(f"  ch03: 2 figures saved")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end