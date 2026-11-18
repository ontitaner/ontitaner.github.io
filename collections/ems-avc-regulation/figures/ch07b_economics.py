# @AI_GENERATED
"""第 07b 章配图：SVG vs 储能无功的全寿命经济决策 + 盈亏平衡分析。

参数对齐章节 07b.1~07b.4：[教学示例]
机会成本 = Q²/(2S) × H × ΔP × η
- S=50 MVA, H=4000h, ΔP=0.5 元/kWh, η=0.9
- SVG 全寿命 230 万 vs 储能机会成本 1800 万
- 盈亏平衡 Q_avg ≈ 3.6 Mvar
"""
from __future__ import annotations

import numpy as np

from _style import (C_OK, C_ACC, C_TARGET, C_LIMIT,
                    C_SVG, C_PCS, C_PURPLE,
                    IMG_DIR, save, note, plt)


def fig_svg_vs_storage():
    years = np.arange(1, 11)
    svg_cum = 180 + 5 * years
    sto_cum_high = 400 * years
    sto_cum_low = 180 * years
    sto_cum_high[5:] += 300
    sto_cum_low[5:] += 300

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))

    ax = axes[0]
    ax.plot(years, svg_cum / 10000, color=C_SVG, lw=2.8, marker="o", ms=6, label="SVG (初投 180 万)")
    ax.plot(years, sto_cum_high / 10000, color=C_LIMIT, lw=2.8, marker="s", ms=6,
            label="储能 Q (年损失 400 万)")
    ax.plot(years, sto_cum_low / 10000, color=C_PCS, lw=2.5, marker="^", ms=6, ls="--",
            label="储能 Q (年损失 180 万)")
    note(ax, "SVG 10 年 230 万\n成本极低", (10, svg_cum[-1] / 10000), (6.5, 0.38))
    note(ax, "储能 Q 大方案\n10 年超 4000 万", (10, sto_cum_high[-1] / 10000), (7.5, 0.2))
    ax.set_xlabel("年份")
    ax.set_ylabel("累计成本 (亿元)")
    ax.set_title("10 年全寿命累计成本", fontsize=10)
    ax.legend(fontsize=8)
    ax.set_ylim(0, 0.45)

    ax = axes[1]
    q_avg = np.linspace(0, 20, 200)
    S, H, dp, eta = 50, 4000, 0.5, 0.9
    annual_loss = q_avg**2 / (2 * S) * H * dp * eta / 10000
    svg_ann = 23

    ax.plot(q_avg, annual_loss, color=C_LIMIT, lw=2.5)
    ax.axhline(svg_ann, color=C_SVG, ls="--", lw=2, label=f"SVG 年化 {svg_ann} 万")
    ax.axvline(3.6, color=C_OK, ls=":", lw=1.5)
    note(ax, f"盈亏平衡\nQ_avg≈3.6 Mvar", (3.6, svg_ann), (6, 70))
    ax.text(1.5, 160, "SVG 不划算", fontsize=9, color=C_OK)
    ax.text(12, 160, "SVG 必须投", fontsize=9, color=C_LIMIT)
    ax.set_xlabel("长期平均无功 Q_avg (Mvar)")
    ax.set_ylabel("年成本 (万元)")
    ax.set_title("盈亏平衡：Q_avg 多大时投 SVG？\nS=50 MVA, H=4000h, ¥0.5/kWh", fontsize=10)
    ax.legend(fontsize=8.5)
    ax.set_ylim(0, 200)

    fig.suptitle("SVG vs 储能无功：全寿命经济决策  [教学示例]", fontsize=11)
    save(fig, "ch07b_svg_vs_storage")


def main():
    fig_svg_vs_storage()
    print(f"  ch07b: saved")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end