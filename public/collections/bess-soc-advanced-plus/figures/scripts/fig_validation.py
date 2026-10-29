# @AI_GENERATED
"""第21章 业务回放证据图 img/ch10_business_replay_evidence.png。"""
import random

from _figstyle import plt, save, C_DIS, C_ACC, C_CHG
import ch10_business_replay as replay

random.seed(replay.REPLAY_CONFIG.random_seed)
report = replay.build_replay_report()

labels = ("计划", "能力下界", "实际")
power_values = (report.plan_power_kw,
                report.minimum_available_power_kw,
                report.minimum_available_power_kw)
energy_values = (report.plan_energy_kwh,
                 report.minimum_available_energy_kwh,
                 report.actual_energy_kwh)
colors = (C_DIS, C_ACC, C_CHG)

fig, (power_ax, energy_ax) = plt.subplots(1, 2, figsize=(10, 4.4))
for ax, values, unit, title in (
    (power_ax, power_values, "功率 (kW)", "功率：计划 / 能力下界 / 实际"),
    (energy_ax, energy_values, "能量 (kWh)", "能量：计划 / 能力下界 / 实际"),
):
    bars = ax.bar(labels, values, color=colors, width=0.6)
    ax.set_ylabel(unit)
    ax.set_title(title)
    ax.set_ylim(0, max(values) * 1.2)
    for bar, value in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, value, f"{value:.0f}",
                ha="center", va="bottom", fontsize=9)

save(fig, "ch10_business_replay_evidence",
     title="业务回放：最低簇能量下界使 2 MW、30 min 计划出现缺口（缺口 −75 kWh）")
# @AI_GENERATED: end