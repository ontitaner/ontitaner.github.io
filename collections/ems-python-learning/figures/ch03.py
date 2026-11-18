# @AI_GENERATED
"""第 03 章配图：单次套利收益分解（瀑布图）、价差与净收益的盈亏平衡图。

电价、效率、退化成本均为 [教学示例]，不代表任何地区的实际政策，以当地最新政策为准。
所有数字由 lab/ems_lab/economics.py 计算，与正文手算、测试一致。
"""
from __future__ import annotations

import json

import numpy as np

from _style import C_ACC, C_CHG, C_DIS, C_GRID, C_LIMIT, C_OK, C_PURPLE, IMG_DIR, plt, save
from ems_lab.economics import arbitrage_cycle, breakeven_spread, net_profit_per_kwh

E_DIS = 1800.0  # 每次放电电量 kWh
P_PEAK, P_VALLEY, P_FLAT = 1.10, 0.30, 0.65  # 元/kWh
ETA = 0.85
C_DEG = 0.10  # 元/kWh（按放电量折算）


def manifest(name: str, numbers: list[float]) -> None:
    (IMG_DIR / f"{name}.json").write_text(
        json.dumps({"figure": f"{name}.png", "numbers": sorted(set(float(n) for n in numbers))}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def fig_waterfall():
    r = arbitrage_cycle(E_DIS, P_PEAK, P_VALLEY, ETA, C_DEG)
    steps = [
        ("放电收入\n1800 kWh × 1.10", r.discharge_revenue, C_DIS),
        ("充电成本\n（若无损耗）\n1800 kWh × 0.30", -r.ideal_charge_cost, C_CHG),
        ("效率损失\n多充 317.6 kWh\n× 0.30", -r.efficiency_loss_cost, C_PURPLE),
        ("退化成本\n1800 kWh × 0.10", -r.degradation_cost, C_ACC),
    ]
    fig, ax = plt.subplots(figsize=(8.6, 4.8))
    level = 0.0
    xs = np.arange(len(steps) + 1)
    for i, (label, value, color) in enumerate(steps):
        bottom = level if value >= 0 else level + value
        ax.bar(i, abs(value), bottom=bottom, color=color, alpha=0.85, width=0.6)
        sign = "+" if value >= 0 else "−"
        ax.text(i, bottom + abs(value) + 25, f"{sign}{abs(value):,.1f}", ha="center", va="bottom", fontsize=10)
        new_level = level + value
        ax.plot([i + 0.3, i + 0.7], [new_level, new_level], color=C_GRID, lw=1, ls=":")
        level = new_level
    ax.bar(len(steps), r.net_profit, color=C_OK, alpha=0.9, width=0.6)
    ax.text(len(steps), r.net_profit + 25, f"= {r.net_profit:,.1f}", ha="center", va="bottom",
            fontsize=10.5, fontweight="bold")
    ax.axhline(r.gross_profit, color=C_GRID, ls="--", lw=0.8)
    ax.text(len(steps), r.gross_profit + 20, f"电费差（未扣退化）{r.gross_profit:,.1f}", ha="center",
            va="bottom", fontsize=8.8, color=C_GRID)
    ax.set_xticks(xs)
    ax.set_xticklabels([s[0] for s in steps] + ["净收益"], fontsize=9)
    ax.set_ylabel("金额（元/次）")
    ax.set_ylim(0, 2250)
    ax.set_xlim(-0.5, len(steps) + 0.85)
    ax.grid(axis="x", visible=False)
    ax.set_title("一次“谷充峰放”的收益分解（1 MW / 2 MWh，η=0.85）\nE_ch=2117.6 kWh，充电总成本=635.3 元  [教学示例]")
    save(fig, "ch03_arbitrage_waterfall")
    manifest("ch03_arbitrage_waterfall", [0.10, 0.30, 0.85, 1.10, 95.3, 180, 317.6, 540, 635.3, 1164.7, 1344.7, 1800, 1980, 2117.6])


def fig_breakeven():
    spread = np.linspace(0, 1.0, 201)
    cases = [
        ("谷电充 0.30，η=0.85，退化 0.10（基准）", P_VALLEY, 0.85, 0.10, C_OK, "-"),
        ("谷电充 0.30，η=0.85，不计退化", P_VALLEY, 0.85, 0.0, C_GRID, "--"),
        ("平电充 0.65，η=0.85，退化 0.10", P_FLAT, 0.85, 0.10, C_PURPLE, "-"),
        ("谷电充 0.30，η=0.75，退化 0.10（效率差）", P_VALLEY, 0.75, 0.10, C_DIS, "-."),
    ]
    fig, ax = plt.subplots(figsize=(8.6, 5.0))
    ax.axhline(0, color="k", lw=0.9)
    ax.axhspan(-0.4, 0, color=C_LIMIT, alpha=0.05)
    ax.text(0.99, -0.33, "亏损区：充放一次反而赔钱", ha="right", color=C_LIMIT, fontsize=9)
    for label, p_ch, eta, c_deg, color, ls in cases:
        y = [net_profit_per_kwh(p_ch + s, p_ch, eta, c_deg) for s in spread]
        ax.plot(spread, y, color=color, ls=ls, lw=2, label=label)
        be = breakeven_spread(p_ch, eta, c_deg)
        ax.plot([be], [0], "o", color=color, ms=6)
    # 标注基准线的盈亏平衡价差与示例点
    be0 = breakeven_spread(P_VALLEY, ETA, C_DEG)
    ax.annotate(f"盈亏平衡价差 {be0:.3f} 元\n（不是 0.10）", xy=(be0, 0), xytext=(0.05, 0.28),
                arrowprops=dict(arrowstyle="->", color=C_OK), fontsize=9, color=C_OK)
    be_flat = breakeven_spread(P_FLAT, ETA, C_DEG)
    ax.annotate(f"平电充电：{be_flat:.3f} 元", xy=(be_flat, 0), xytext=(0.30, -0.20),
                arrowprops=dict(arrowstyle="->", color=C_PURPLE), fontsize=9, color=C_PURPLE)
    s_ex = P_PEAK - P_VALLEY
    y_ex = net_profit_per_kwh(P_PEAK, P_VALLEY, ETA, C_DEG)
    ax.plot([s_ex], [y_ex], "s", color=C_OK, ms=8)
    ax.annotate(f"本章例子：价差 0.80 元\n每 kWh 净赚 {y_ex:.3f} 元\n× 1800 kWh = {y_ex * E_DIS:,.1f} 元",
                xy=(s_ex, y_ex), xytext=(0.66, 0.14), arrowprops=dict(arrowstyle="->"), fontsize=9,
                bbox=dict(fc="white", ec=C_GRID, alpha=0.9, boxstyle="round,pad=0.25"))
    ax.set_xlim(0, 1.0)
    ax.set_ylim(-0.4, 0.95)
    ax.set_xlabel("价差 = 放电电价 − 充电电价（元/kWh）")
    ax.set_ylabel("每放出 1 kWh 的净收益（元）")
    ax.set_title("价差多大才值得充放？净收益 = 放电电价 − 充电电价/η − 退化成本  [教学示例]")
    ax.legend(loc="upper left", fontsize=8.6, bbox_to_anchor=(0.0, 1.0))
    save(fig, "ch03_breakeven")
    manifest("ch03_breakeven", [0.053, 0.10, 0.153, 0.20, 0.215, 0.30, 0.65, 0.75, 0.80, 0.85, 1.10, 0.647, 1164.7, 1800])


def main():
    fig_waterfall()
    fig_breakeven()


if __name__ == "__main__":
    main()
# @AI_GENERATED: end
