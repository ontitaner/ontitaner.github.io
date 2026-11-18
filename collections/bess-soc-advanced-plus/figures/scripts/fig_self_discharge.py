# @AI_GENERATED
"""图：自放电 — 温度相关衰减 + 安时积分盲区 + 修正效果对比。"""
from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt

from _figstyle import C_CHG, C_DIS, C_GRID, C_OK, C_LIMIT, IMG_DIR, plt, save

def main():
    np.random.seed(42)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.8))
    fig.suptitle("自放电：温度相关的无电流 SOC 衰减 & 安时积分盲区",
                 fontsize=13, y=0.98)

    base_rate = 3.0  # %/月 at 25C
    days = 7
    t_h = np.linspace(0, days * 24, 500)

    def rate(temp_c):
        return base_rate / (30 * 24) * (2 ** ((temp_c - 25) / 10))

    # ── 左栏：三温度衰减曲线 ──
    colors_t = {25: C_CHG, 35: C_DIS, 45: C_LIMIT}
    labels_t = {
        25: r"25°C ($3\%$/月) − 一周跌 $0.70$ pp",
        35: r"35°C ($6\%$/月) − 一周跌 $1.40$ pp",
        45: r"45°C ($12\%$/月) − 一周跌 $2.80$ pp",
    }

    for tc in [25, 35, 45]:
        loss = rate(tc) * t_h
        ax1.plot(t_h, loss, color=colors_t[tc], lw=2.0, label=labels_t[tc])

    ax1.set_xlabel("静置时间 (h)")
    ax1.set_ylabel("SOC 损失 (百分点)")
    ax1.set_title("左栏：不同温度下自放电累积损失", fontsize=11)
    ax1.legend(fontsize=9, framealpha=0.9)

    for day in [1, 3, 7]:
        ax1.axvline(x=day * 24, color=C_GRID, lw=0.6, ls=":", alpha=0.5)

    for tc, d, x, yoff in [(25, 7, 168, 0.12), (35, 7, 168, 0.12), (45, 7, 168, 0.12)]:
        v = rate(tc) * d * 24
        ax1.annotate(f"{v:.2f} pp", xy=(d * 24, v), fontsize=8.5, color=colors_t[tc],
                     xytext=(d * 24 + 3, v + yoff),
                     arrowprops=dict(arrowstyle="->", color=colors_t[tc], lw=0.8))

    # ── 右栏：修正效果对比 ──
    soc_start = 23.0
    temp = 35
    b = rate(temp)
    days_rest = 7
    t_h2 = np.linspace(0, days_rest * 24, 400)

    soc_true = soc_start - b * t_h2
    soc_ah = np.full_like(t_h2, soc_start)
    soc_corrected = soc_start - b * t_h2

    ax2.plot(t_h2, soc_ah, color=C_DIS, lw=2.2, ls="--",
             label="安时积分（无修正：停在 $23.0\\%$）")
    ax2.plot(t_h2, soc_true, color="black", lw=2.2, label="真实 SOC（含自放电）")
    ax2.plot(t_h2, soc_corrected, color=C_CHG, lw=2.2, ls="-.",
             label="修正后积分（≈ 真实值）")

    ax2.set_xlabel("静置时间 (h)")
    ax2.set_ylabel("SOC (%)")
    ax2.set_title("右栏：安时积分盲区 — 自放电没有电流，积分不更新", fontsize=11)
    ax2.legend(fontsize=9, framealpha=0.9)

    ax2.fill_between(t_h2, soc_ah, soc_true, color=C_DIS, alpha=0.10, lw=0)

    ax2.annotate("$0.70$ pp 偏差\n无电流信号可修正",
                 xy=(168, soc_start - b * 168), fontsize=9.5, color=C_DIS, ha="left",
                 xytext=(90, soc_start - 0.6),
                 arrowprops=dict(arrowstyle="->", color=C_DIS, lw=1.0))

    ax2.set_ylim(21.0, 23.5)

    save(fig, "self_discharge")

if __name__ == "__main__":
    main()