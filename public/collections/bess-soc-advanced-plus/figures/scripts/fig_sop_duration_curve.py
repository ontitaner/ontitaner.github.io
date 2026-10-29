# @AI_GENERATED
"""第17章：任务时长决定SOP瓶颈。"""
from _figstyle import plt, save, C_CHG, C_DIS, C_OK, C_GRID

soe_kwh = 644.4
minutes = list(range(5, 121))
energy_limit = [soe_kwh / (m/60.0) for m in minutes]
bms, pcs, grid = 2200.0, 2500.0, 2000.0
sop = [min(p, bms, pcs, grid) for p in energy_limit]

fig, ax = plt.subplots(figsize=(9.2, 4.7))
ax.plot(minutes, energy_limit, color=C_CHG, lw=2, label="能量约束功率")
ax.axhline(bms, color=C_OK, ls="--", label="BMS 限值 2200 kW")
ax.axhline(pcs, color=C_GRID, ls="--", label="PCS 限值 2500 kW")
ax.axhline(grid, color=C_DIS, ls="--", label="并网出口 2000 kW")
ax.plot(minutes, sop, color="black", lw=2.6, label="最终 SOP")
for m, label in [(10, "10 min：并网瓶颈"), (30, "30 min：能量瓶颈"), (60, "60 min：能量瓶颈")]:
    value = min(soe_kwh/(m/60.0), bms, pcs, grid)
    ax.scatter([m], [value], color=C_DIS, zorder=3)
    ax.annotate(f"{label}\nSOP={value:.0f} kW", (m, value), (m+5, value+180), fontsize=8.5,
                arrowprops=dict(arrowstyle="->", color=C_DIS))
ax.set(xlabel="任务持续时间 (min)", ylabel="可承诺放电功率 (kW)",
       title="同一 644.4 kWh 能量余额下，任务越长，SOP 越受能量限制")
ax.set_ylim(0, 4200)
ax.legend(loc="upper right", fontsize=8.5)

save(fig, "sop_duration_curve", title="任务时长—持续功率：30 min 任务只能承诺 1289 kW")
# @AI_GENERATED: end