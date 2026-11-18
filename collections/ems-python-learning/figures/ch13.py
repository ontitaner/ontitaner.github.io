# @AI_GENERATED
"""第 13 章配图：分时电价 + 充放电计划 + SOC；价差与单次净收益。

曲线直接调用 lab/ems_lab/arbitrage.py 的实现生成。电价、效率、退化成本均为 [教学示例]。
"""
from __future__ import annotations

import json

import numpy as np

from _style import C_ACC, C_CHG, C_DIS, C_GRID, C_LIMIT, C_OK, C_PURPLE, IMG_DIR, plt, save
from ems_lab.arbitrage import (
    BatterySpec,
    TouPeriod,
    cycle_net_profit,
    greedy_plan,
    rule_based_plan,
    spread_threshold,
    tou_prices,
    validate_plan,
)

PERIODS = [
    TouPeriod(0, 8, "谷", 0.30),
    TouPeriod(8, 11, "峰", 1.10),
    TouPeriod(11, 13, "平", 0.65),
    TouPeriod(13, 15, "谷", 0.30),
    TouPeriod(15, 17, "平", 0.65),
    TouPeriod(17, 19, "峰", 1.10),
    TouPeriod(19, 21, "尖峰", 1.35),
    TouPeriod(21, 24, "平", 0.65),
]
BAT = BatterySpec(capacity_kwh=4000, p_max_charge_kw=1000, p_max_discharge_kw=1000,
                  soc_min=0.10, soc_max=0.90, eta_charge=0.92, eta_discharge=0.92)
DEG = 0.10
COLORS = {"谷": C_CHG, "平": C_GRID, "峰": C_DIS, "尖峰": C_LIMIT}


def manifest(name: str, numbers: list[float]) -> None:
    payload = {"_comment": "@AI_GENERATED", "figure": f"{name}.png",
               "numbers": sorted(set(float(n) for n in numbers)),
               "_comment_end": "@AI_GENERATED: end"}
    (IMG_DIR / f"{name}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def fig_tou_plan():
    prices = tou_prices(PERIODS)
    h = np.arange(96) * 0.25
    g = greedy_plan(prices, BAT, soc0=0.10, degradation_cost_per_kwh=DEG)
    ok = validate_plan(g.plan_kw, BAT, soc0=0.10)
    rule = rule_based_plan(prices, BAT, charge_at_or_below=0.30, discharge_at_or_above=1.10)
    bad = validate_plan(rule, BAT, soc0=0.10)

    fig, axes = plt.subplots(3, 1, figsize=(10, 8.4), sharex=True, gridspec_kw={"height_ratios": [0.9, 1.6, 1.4]})
    ax = axes[0]
    for p in PERIODS:
        ax.bar((p.start_h + p.end_h) / 2, p.price, width=p.end_h - p.start_h, color=COLORS[p.name], alpha=0.55,
               edgecolor="white")
        ax.text((p.start_h + p.end_h) / 2, p.price + 0.05, f"{p.name}\n{p.price:.2f}", ha="center", fontsize=8.5)
    ax.set_ylabel("电价\n(元/kWh)")
    ax.set_ylim(0, 1.75)
    ax.set_title("分时电价、贪心排程计划与 SOC 轨迹（储能 1 MW / 4 MWh）  [教学示例]", fontsize=10)

    ax = axes[1]
    plan = np.array(g.plan_kw)
    ax.bar(h + 0.125, np.where(plan > 0, plan, 0), width=0.25, color=C_DIS, alpha=0.75, label="计划放电 (P>0)")
    ax.bar(h + 0.125, np.where(plan < 0, plan, 0), width=0.25, color=C_CHG, alpha=0.75, label="计划充电 (P<0)")
    ax.step(np.append(h, 24), np.append(rule, rule[-1]), where="post", color=C_GRID, lw=1.2, ls="--",
            label="简单规则（谷充峰放、不看 SOC）")
    ax.axhline(0, color="k", lw=0.8)
    ax.set_ylabel("储能功率 (kW)")
    ax.set_ylim(-1500, 1500)
    ax.legend(loc="lower center", ncol=3, fontsize=8.5)
    notes = [(1.7, "①谷充"), (9.5, "②早峰放"), (12.0, "③平充"), (14.0, "④谷充"), (19.5, "⑤晚峰/尖峰放")]
    for x, s in notes:
        ax.text(x, 1150, s, ha="center", fontsize=9)

    ax = axes[2]
    ax.plot(np.arange(97) * 0.25, np.array(bad.soc) * 100, color=C_GRID, lw=1.5, ls="--",
            label="简单规则：SOC 超过 100%，计划不可执行")
    ax.plot(np.arange(97) * 0.25, np.array(ok.soc) * 100, color=C_OK, lw=2.3,
            label=f"贪心排程：始终在 10%～90%，日末回到起点，预期收益 {g.expected_profit:,.0f} 元")
    ax.axhline(BAT.soc_max * 100, color=C_LIMIT, ls=":", lw=1)
    ax.axhline(BAT.soc_min * 100, color=C_LIMIT, ls=":", lw=1)
    ax.axhline(100, color=C_LIMIT, lw=1)
    ax.text(23.9, 86, "SOC 上限 90%", ha="right", va="top", fontsize=8.5, color=C_LIMIT)
    ax.text(23.9, 103, "100%", ha="right", va="bottom", fontsize=8.5, color=C_LIMIT)
    ax.text(19.6, 13, "SOC 下限 10%", ha="right", va="bottom", fontsize=8.5, color=C_LIMIT)
    ax.set_ylabel("SOC (%)")
    ax.set_ylim(0, 240)
    ax.set_xlabel("时刻 (h)，96 点 × 15 分钟")
    ax.set_xticks(range(0, 25, 2))
    ax.legend(loc="upper left", fontsize=8.5)
    save(fig, "ch13_tou_plan")
    manifest("ch13_tou_plan", [0.3, 0.65, 1, 1.1, 1.35, 4, 10, 90, 96, 100, 3784])


def fig_spread_profit():
    spread = np.linspace(0, 1.0, 201)
    fig, ax = plt.subplots(figsize=(9, 4.6))
    cases = [
        (0.30, 0.85, 0.10, C_DIS, "谷 0.30 充，η=85%，退化 0.10"),
        (0.30, 0.85, 0.00, C_ACC, "谷 0.30 充，η=85%，不计退化"),
        (0.65, 0.85, 0.10, C_PURPLE, "平 0.65 充，η=85%，退化 0.10"),
    ]
    for pc, eta, deg, color, label in cases:
        net = [cycle_net_profit(1.0, pc + s, pc, eta, deg).net for s in spread]
        ax.plot(spread, net, color=color, lw=2.2, label=label)
        th = spread_threshold(pc, eta, deg)
        ax.plot(th, 0, "o", color=color, ms=7, zorder=5)
        ax.plot([th, th], [0, -0.27], color=color, lw=0.8, ls=":")
        ax.text(th, -0.28, f"门槛\n{th:.3f}", ha="center", va="top", color=color, fontsize=8.5)
    # (价差, 充电价, 名称, 标注文字位置)
    examples = [(0.80, 0.30, "谷→峰 0.80", (0.86, 0.42)), (0.45, 0.65, "平→峰 0.45", (0.60, 0.07)),
                (0.35, 0.30, "谷→平 0.35", (0.20, 0.46))]
    for s, pc, name, pos in examples:
        v = cycle_net_profit(1.0, pc + s, pc, 0.85, 0.10).net
        ax.plot(s, v, "s", color="k", ms=6, zorder=6)
        ax.annotate(f"{name}\n净 {v:.3f} 元/kWh", xy=(s, v), xytext=pos, ha="center", fontsize=8.5,
                    arrowprops=dict(arrowstyle="->", color="k", lw=0.8))
    ax.axhline(0, color="k", lw=0.9)
    ax.axhspan(-0.4, 0, color=C_LIMIT, alpha=0.06)
    ax.text(0.99, -0.36, "亏损区：价差不够覆盖损耗和寿命消耗", ha="right", fontsize=9, color=C_LIMIT)
    ax.set_xlabel("价差 = 放电电价 − 充电电价 (元/kWh)")
    ax.set_ylabel("每放 1 kWh 的净收益 (元)")
    ax.set_xlim(0, 1.0)
    ax.set_ylim(-0.4, 0.8)
    ax.set_title("价差 vs 单次净收益：有价差不等于赚钱  [教学示例参数]", fontsize=10)
    ax.legend(loc="upper left", fontsize=8.5)
    save(fig, "ch13_spread_profit")
    manifest("ch13_spread_profit", [0.053, 0.1, 0.153, 0.197, 0.215, 0.235, 0.3, 0.35, 0.45, 0.647, 0.65, 0.8, 0.85])


def main():
    fig_tou_plan()
    fig_spread_profit()


if __name__ == "__main__":
    main()
# @AI_GENERATED: end
