# @AI_GENERATED
"""第 05 章配图：两充两放日前排程（电价 + SOC 轨迹）。

参数对齐章节 05.2：[教学示例]
- 谷充 80MWh（2–4 点）、峰放（10–12 点）、平充 80MWh（14–16 点）、峰放（18–20 点）
- SOC 10% ↔ 90%，电池侧功率 40 MW（并网侧充电 42.1 MW、放电 38 MW）
"""
from __future__ import annotations

import numpy as np

from _style import C_PRICE, C_SOC, C_DIS, C_CHG, C_GRID, save, note, plt

PRICES = [0.35] * 8 + [0.70] * 2 + [1.20] * 2 + [0.70] * 5 + [1.20] * 4 + [0.70] * 2 + [0.35]


def _soc_trace():
    # SOC 分段线性：10% ↔ 90%
    seg = [0.10] * 2          # 0-2 待命
    seg += [0.50, 0.90]       # 2-4 充电（2h 40MW）
    seg += [0.90] * 6         # 4-10
    seg += [0.50, 0.10]       # 10-12 放电
    seg += [0.10] * 2         # 12-14
    seg += [0.50, 0.90]       # 14-16 充电
    seg += [0.90] * 2         # 16-18
    seg += [0.50, 0.10]       # 18-20 放电
    seg += [0.10] * 4         # 20-24
    return np.array(seg)


def fig_schedule():
    hours = np.arange(24)
    prices = np.array(PRICES)
    soc = _soc_trace()

    fig, ax1 = plt.subplots(figsize=(11, 5.2))
    colors = [C_CHG if p == 0.35 else (C_DIS if p == 1.20 else C_GRID) for p in prices]
    ax1.bar(hours, prices, color=colors, width=0.72, alpha=0.85)
    ax1.set_xlabel("小时 (h)")
    ax1.set_ylabel("电价 (元/kWh)", color=C_PRICE)
    ax1.set_ylim(0, 1.4)
    ax1.set_xticks(hours)

    ax2 = ax1.twinx()
    ax2.plot(hours, soc * 100, color=C_SOC, lw=2.6, marker="o", ms=4)
    ax2.set_ylabel("SOC (%)", color=C_SOC)
    ax2.set_ylim(0, 105)

    ax1.axvspan(2, 4, color=C_CHG, alpha=0.10)
    ax1.axvspan(10, 12, color=C_DIS, alpha=0.10)
    ax1.axvspan(14, 16, color=C_CHG, alpha=0.10)
    ax1.axvspan(18, 20, color=C_DIS, alpha=0.10)
    note(ax1, "谷充 40MW(电池侧)×2h\n+80MWh", (3, 0.35), (4.6, 0.78))
    note(ax1, "峰放 40MW(电池侧)×2h\n−80MWh→并网76", (11, 1.20), (5.2, 1.06))
    note(ax1, "平充 40MW(电池侧)×2h\n+80MWh", (15, 0.70), (12.5, 0.48))
    note(ax1, "峰放 40MW(电池侧)×2h\n−80MWh→并网76", (19, 1.20), (15.2, 1.06))

    ax1.set_title("两充两放日前排程：谷充→峰放、平充→峰放  [教学示例]")
    save(fig, "ch05_schedule")


def main():
    fig_schedule()
    print("  ch05: 1 figure saved")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end