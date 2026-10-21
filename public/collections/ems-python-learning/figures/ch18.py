# @AI_GENERATED
"""第 18 章配图：各自限幅相加 vs 合成后投影、离线重分配、SOC 均衡分配前后各簇 SOC。

数值由 lab/ems_lab/arbitration.py、allocation.py 算出，参数为 [教学示例]。
"""
from __future__ import annotations

import json

import numpy as np

from _style import C_ACC, C_CHG, C_DIS, C_GRID, C_LIMIT, C_OK, C_PURPLE, IMG_DIR, plt, save
from ems_lab.allocation import Unit, allocate_by_capability, simulate_soc
from ems_lab.arbitration import Priority, Request, arbitrate, device_limit, naive_limit_each_then_sum

CAP = device_limit(500, 800)  # 允许 [−500, +800] kW


def manifest(name: str, numbers: list[float]) -> None:
    payload = {"_comment": "@AI_GENERATED", "figure": f"{name}.png",
               "numbers": sorted(set(float(n) for n in numbers)),
               "_comment_end": "@AI_GENERATED: end"}
    (IMG_DIR / f"{name}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def fig_limit_vs_project():
    cases = [
        ("同向：计划 +600，一次调频 +300", [Request("计划", Priority.P3_DISPATCH, 600),
                                         Request("一次调频", Priority.P3_DISPATCH, 300, "delta")]),
        ("反向：计划 +900，一次调频 −300", [Request("计划", Priority.P3_DISPATCH, 900),
                                         Request("一次调频", Priority.P3_DISPATCH, -300, "delta")]),
    ]
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), sharey=True)
    for ax, (title, reqs) in zip(axes, cases):
        want = sum(r.p_kw for r in reqs)
        naive = naive_limit_each_then_sum(reqs, [CAP])
        res = arbitrate(reqs, [CAP])
        vals = [want, naive, res.final_kw]
        names = ["合成请求\n（投影前）", "错误：各自限幅\n再相加", "正确：合成后\n统一投影一次"]
        colors = [C_GRID, C_LIMIT, C_OK]
        bars = ax.bar(range(3), vals, color=colors, width=0.6)
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v + 20, f"{v:.0f} kW", ha="center")
        ax.axhline(800, color=C_LIMIT, ls="--", lw=1.2)
        ax.text(-0.35, 1000, "红虚线：可放上限 800 kW", color=C_LIMIT, fontsize=9)
        if naive > 800:
            ax.text(1, 380, "超出设备能力\n100 kW", ha="center", color="white", fontsize=9.5)
        elif naive < res.final_kw:
            ax.text(1, 250, "本可执行 600，\n却少放了 100 kW", ha="center", color="white", fontsize=9.5)
        if abs(res.unserved_kw) > 1e-6:
            ax.text(2, 360, f"未满足 {res.unserved_kw:.0f} kW\n原因：\n{res.limiting[0]}", ha="center", color="white",
                    fontsize=9)
        else:
            ax.text(2, 250, "未满足 0 kW", ha="center", color="white", fontsize=9.5)
        ax.set_xticks(range(3))
        ax.set_xticklabels(names)
        ax.set_title(title)
        ax.set_ylim(0, 1050)
    axes[0].set_ylabel("储能有功 (kW，放电为正)")
    fig.suptitle("为什么先合成、后统一投影：各自限幅相加，同向会超限、反向会少放  [教学示例]", y=1.02)
    manifest("ch18_limit_vs_project", [-500, -300, 100, 300, 500, 600, 800, 900])
    save(fig, "ch18_limit_vs_project")


def fig_offline_realloc():
    units = [Unit("PCS1", 400, 400), Unit("PCS2", 300, 300), Unit("PCS3", 200, 200), Unit("PCS4", 100, 100)]
    before = allocate_by_capability(800, units)
    units[0].online = False
    after = allocate_by_capability(800, units)
    names = [u.name for u in units]
    x = np.arange(len(names))
    fig, ax = plt.subplots(figsize=(9, 4.6))
    cap = [400, 300, 200, 100]
    ax.bar(x - 0.2, cap, 0.38, color="none", edgecolor=C_GRID, ls="--", lw=1.2)
    ax.bar(x + 0.2, [0] + cap[1:], 0.38, color="none", edgecolor=C_GRID, ls="--", lw=1.2, label="单机可放能力")
    b1 = ax.bar(x - 0.2, [before.setpoints[n] for n in names], 0.38, color=C_CHG, label="全部在线：按能力比例")
    b2 = ax.bar(x + 0.2, [after.setpoints[n] for n in names], 0.38, color=C_DIS, label="PCS1 离线后重新分配")
    for b in list(b1) + list(b2):
        h = b.get_height()
        ax.text(b.get_x() + b.get_width() / 2, h + 8, f"{h:.0f}", ha="center", fontsize=9)
    ax.text(0.2, 40, "离线\n能力置 0", ha="center", fontsize=9, color=C_DIS)
    ax.text(3.3, 330, f"总指令 800 kW\n重分配后只能给 {after.allocated_kw:.0f} kW\n未满足 {after.unserved_kw:.0f} kW → 上报",
            ha="center", fontsize=9.5, bbox=dict(fc="white", ec=C_LIMIT))
    ax.set_xticks(x)
    ax.set_xticklabels(names)
    ax.set_ylabel("放电功率 (kW)")
    ax.set_ylim(0, 470)
    ax.set_title("按可用能力比例分配，离线设备能力置零并重新分配  [教学示例]")
    ax.legend(loc="upper center", ncol=3, fontsize=8.5)
    manifest("ch18_offline_realloc", [0, 100, 200, 300, 400, 600, 800])
    save(fig, "ch18_offline_realloc")


def fig_soc_balance():
    units = [Unit(f"簇{i + 1}", 250, 250, soc=s, energy_kwh=1000) for i, s in enumerate((0.9, 0.7, 0.6, 0.4))]
    runs = [
        ("按能力比例（均分）", "capability", 1.0),
        ("SOC 均衡 γ=1（按剩余电量加权）", "soc", 1.0),
        ("SOC 均衡 γ=2（高 SOC 更多放）", "soc", 2.0),
    ]
    colors = [C_DIS, C_ACC, C_OK, C_CHG]
    fig, axes = plt.subplots(2, 2, figsize=(12, 7.2), sharex=True)
    delivered = {}
    for ax, (title, method, g) in zip(axes.flat[:3], runs):
        t, socs, unserved = simulate_soc(units, 600, 4 * 3600, 60, method, gamma=g)
        th = np.array(t) / 3600
        for (name, s), c in zip(socs.items(), colors):
            ax.plot(th, np.array(s) * 100, color=c, lw=2, label=name)
        ax.axhline(5, color=C_LIMIT, ls="--", lw=1)
        ax.set_title(title, fontsize=10.5)
        ax.set_ylabel("SOC (%)")
        ax.set_ylim(0, 100)
        delivered[title] = 600 - np.array(unserved)
    axes[0, 0].legend(loc="upper right", fontsize=8.5, ncol=2)
    axes[0, 0].annotate("簇4 最先放空（约 2.3 h）", xy=(2.33, 5), xytext=(0.05, 11), fontsize=9,
                        arrowprops=dict(arrowstyle="->"))
    axes[0, 1].text(0.2, 12, "各簇剩余电量按同一比例减少，同时到达下限", fontsize=9)
    axes[1, 0].text(0.2, 12, "SOC 差距更快收敛", fontsize=9)
    ax = axes[1, 1]
    for (title, _, _), c, ls in zip(runs, [C_DIS, C_ACC, C_OK], ["-", "-", "--"]):
        ax.plot(th, delivered[title], color=c, lw=2, ls=ls, label=title.split("（")[0])
    ax.axhline(600, color=C_GRID, ls=":", lw=1)
    ax.set_ylim(0, 700)
    ax.set_ylabel("全站实际放电 (kW)")
    ax.set_title("全站出力：均分时 SOC 低的簇先退出，约 3.35 h 起满足不了 600 kW", fontsize=10.5)
    ax.legend(loc="lower left", fontsize=8.5)
    for a in axes[1]:
        a.set_xlabel("时间 (h)")
    fig.suptitle("4 簇 × 250 kW / 1000 kWh，初始 SOC 90/70/60/40%，全站恒定放电 600 kW  [教学示例]", y=1.01)
    manifest("ch18_soc_balance", [2.3, 3.35, 4, 40, 60, 70, 90, 250, 600, 1000])
    save(fig, "ch18_soc_balance")


def main():
    fig_limit_vs_project()
    fig_offline_realloc()
    fig_soc_balance()


if __name__ == "__main__":
    main()
# @AI_GENERATED: end
