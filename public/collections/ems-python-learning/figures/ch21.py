# @AI_GENERATED
"""第 21 章配图：综合项目参考实现（lab/ems_lab/mini_ems.py）跑出的一天，以及与对照组的比较。[教学示例]"""
from __future__ import annotations

import json

import numpy as np

from _style import C_ACC, C_CHG, C_DIS, C_GRID, C_LIMIT, C_OK, C_PURPLE, IMG_DIR, plt, save
from ems_lab.arbitrage import tou_prices
from ems_lab.mini_ems import STEPS, baseline_no_storage, run_day


def manifest(name: str, numbers: list[float]) -> None:
    payload = {"_comment": "@AI_GENERATED", "figure": f"{name}.png",
               "numbers": sorted(set(float(n) for n in numbers)),
               "_comment_end": "@AI_GENERATED: end"}
    (IMG_DIR / f"{name}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def fig_day():
    r = run_day()
    cfg = r.cfg
    h = np.arange(STEPS) / 60
    prices = tou_prices(cfg.tou, STEPS)
    fig, axes = plt.subplots(4, 1, figsize=(10, 10), sharex=True, gridspec_kw={"height_ratios": [0.7, 2, 1.6, 1.1]})

    ax = axes[0]
    ax.step(h, prices, where="post", color=C_GRID, lw=2)
    ax.set_ylabel("电价\n(元/kWh)")
    ax.set_ylim(0, 1.4)
    ax.set_title("综合项目：用各章真实模块跑出的一天（1 MW / 4 MWh 光储站，1 分钟周期）  [教学示例]")

    ax = axes[1]
    ax.plot(h, r.load, color="k", lw=1.5, label="负荷")
    ax.fill_between(h, 0, r.pv_used, color=C_ACC, alpha=0.35, label="光伏实际发电")
    ax.fill_between(h, r.pv_used, r.pv, color=C_ACC, alpha=0.12, hatch="//", edgecolor=C_ACC, lw=0,
                    label="光伏限发（储能已满，防倒送兜底）")
    ax.plot(h, r.p_import, color=C_PURPLE, lw=1.8, label="并网点取电 P_import")
    ax.axhline(cfg.demand_goal_kw, color=C_LIMIT, ls="--", lw=1)
    ax.text(0.2, cfg.demand_goal_kw + 50, f"需量目标 {cfg.demand_goal_kw:.0f} kW", color=C_LIMIT, fontsize=9)
    ax.axhline(0, color="k", lw=0.8)
    ax.set_ylabel("功率 (kW)")
    ax.set_ylim(-150, 3300)
    ax.legend(loc="upper right", ncol=2, fontsize=8.5)

    ax = axes[2]
    ax.step(h, r.request, where="post", color=C_GRID, lw=1.2, ls="--", label="日前计划请求")
    p = np.array(r.p_bess)
    ax.fill_between(h, 0, p, where=p > 0, color=C_DIS, alpha=0.6, step="post", label="实际放电")
    ax.fill_between(h, 0, p, where=p < 0, color=C_CHG, alpha=0.6, step="post", label="实际充电")
    ax.axhline(0, color="k", lw=0.8)
    notes = [(1.5, 900, "① 谷时充电\n需量压到约 900 kW"),
             (5.3, 900, "② 夜班设备启动\n需量：小幅放电"),
             (10.0, 900, "③ 光伏富余\n防倒送：放电被压下"),
             (12.6, -1180, "④ 电池充满\n冲突上报，光伏限发")]
    for x, y, t in notes:
        ax.text(x, y, t, ha="center", va="top" if y > 0 else "bottom", fontsize=8.5,
                bbox=dict(fc="white", ec=C_GRID, alpha=0.92, boxstyle="round,pad=0.25"))
    ax.set_ylabel("储能功率 (kW)")
    ax.set_ylim(-1250, 1250)
    ax.legend(loc="lower right", fontsize=8.5, ncol=3)

    ax = axes[3]
    ax.plot(h, np.array(r.soc) * 100, color=C_OK, lw=2.2)
    z = cfg.soc_zones
    for v in (z.stop_discharge_at, z.stop_charge_at):
        ax.axhline(v * 100, color=C_LIMIT, ls=":", lw=1)
    ax.set_ylabel("SOC (%)")
    ax.set_ylim(0, 100)
    ax.set_xlabel("时刻 (h)")
    ax.set_xticks(range(0, 25, 2))
    save(fig, "ch21_day")
    manifest("ch21_day", [1, 4, 20, 85, 90, 900, 1000, 1100, 1750, 1800])


def fig_compare():
    base = baseline_no_storage()
    plan = run_day(use_constraints=False)
    ems = run_day()
    names = ["无储能", "只执行\n日前计划", "EMS\n（计划+实时约束）"]
    metrics = [
        ("15 分钟最大需量 (kW)", [base.max_demand_kw, plan.max_demand_kw(), ems.max_demand_kw()], ems.cfg.demand_goal_kw),
        ("最大倒送功率 (kW)", [0.0, plan.max_backfeed_kw(), ems.max_backfeed_kw()], 0.0),
        ("当日购电电费 (元)", [base.grid_energy_cost, plan.grid_energy_cost(), ems.grid_energy_cost()], None),
        ("弃光电量 (kWh)", [base.pv_curtailed_kwh, plan.pv_curtailed_kwh(), ems.pv_curtailed_kwh()], None),
    ]
    fig, axes = plt.subplots(1, 4, figsize=(13, 4.2))
    colors = [C_GRID, C_ACC, C_OK]
    for ax, (title, vals, limit) in zip(axes, metrics):
        bars = ax.bar(range(3), vals, color=colors, width=0.6, alpha=0.9)
        top = max(max(vals), limit or 0)
        for b, v in zip(bars, vals):
            # 数值写在柱子中部，避免和限值线、限值文字重叠
            y, color = (v / 2, "white") if v > 0.15 * top else (v + 0.02 * top, "k")
            ax.text(b.get_x() + b.get_width() / 2, y, f"{v:,.0f}", ha="center", va="center", fontsize=9.5,
                    color=color, fontweight="bold")
        if limit is not None:
            ax.axhline(limit, color=C_LIMIT, ls="--", lw=1)
            ax.text(-0.45, limit, "限值", color=C_LIMIT, fontsize=8.5, va="bottom", ha="left")
        if title.startswith("弃光"):
            ax.text(1, max(vals) * 0.08, "没弃光，\n但倒送了", ha="center", fontsize=8.5, color=C_LIMIT)
        ax.set_xticks(range(3))
        ax.set_xticklabels(names, fontsize=8.5)
        ax.set_title(title, fontsize=10)
        ax.set_ylim(0, max(max(vals), limit or 0) * 1.18 + 1)
        ax.grid(axis="x", visible=False)
    fig.suptitle("同一天、同一座站：只有计划没有实时约束，需量和倒送都会越限  [教学示例]", y=1.02)
    save(fig, "ch21_compare")
    manifest("ch21_compare", [0, 1331, 1584, 1750, 1800, 1869, 2908, 6593, 7384, 9787])


def main():
    fig_day()
    fig_compare()


if __name__ == "__main__":
    main()
# @AI_GENERATED: end
