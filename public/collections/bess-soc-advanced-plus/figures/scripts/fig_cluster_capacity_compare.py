# @AI_GENERATED
"""第19章：相同平均SOC下，最低簇差异导致不同可用能量。"""
from _figstyle import plt, save, C_CHG, C_DIS, C_OK, C_GRID

scenarios = {
    "一致性良好": [0.55, 0.54, 0.55, 0.54],
    "一致性较差": [0.60, 0.58, 0.55, 0.45],
}
energy_per_cluster = 314.0 * 3.2 * 416 / 1000.0
minimum_soc = .05
fig, axes = plt.subplots(1, 2, figsize=(10.4, 4.4), sharey=True)

for ax, (name, socs) in zip(axes, scenarios.items()):
    colors = [C_CHG if value > min(socs) else C_DIS for value in socs]
    bars = ax.bar(["簇1", "簇2", "簇3", "簇4"], [value*100 for value in socs], color=colors)
    mean_soc = sum(socs)/len(socs)
    usable = len(socs)*(min(socs)-minimum_soc)*energy_per_cluster
    ax.axhline(mean_soc*100, color=C_GRID, ls="--", label=f"平均 SOC={mean_soc:.1%}")
    ax.axhline(minimum_soc*100, color=C_DIS, ls=":", label="放电下限=5%")
    for bar, value in zip(bars, socs):
        ax.text(bar.get_x()+bar.get_width()/2, value*100+1.5, f"{value:.0%}", ha="center", fontsize=9)
    ax.text(1.5, 72, f"最低簇={min(socs):.0%}\n可用能量={usable:.3f} kWh", ha="center", fontsize=9,
            bbox=dict(boxstyle="round,pad=.3", fc="white", ec=C_GRID))
    ax.set_title(name)
    ax.set_xlabel("并联簇")
    ax.legend(loc="lower right", fontsize=8)
axes[0].set_ylabel("簇 SOC (%)")
axes[0].set_ylim(0, 80)

save(fig, "cluster_capacity_compare", title="平均 SOC 均为 54.5%，最低簇不同会使可用能量相差 150.5 kWh")
# @AI_GENERATED: end