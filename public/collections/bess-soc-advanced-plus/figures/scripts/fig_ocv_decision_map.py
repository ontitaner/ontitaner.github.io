# @AI_GENERATED
"""第06章：OCV温度、方向和信息量决定能否修正SOC。"""
from _figstyle import plt, save, C_CHG, C_DIS, C_OK, C_GRID
from soc_core import OCV_SOC, ocv_from_soc, ocv_slope, observation_information

socs = [k / 200 for k in range(201)]
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.4))

for temp, color in [(-10.0, C_GRID), (25.0, C_CHG), (45.0, C_OK)]:
    values = [ocv_from_soc(soc, temp) for soc in socs]
    ax1.plot(socs, values, color=color, label=f"{temp:.0f}°C")
charge = ocv_from_soc(.50, 25.0, "charge", 0.0)
discharge = ocv_from_soc(.50, 25.0, "discharge", 0.0)
ax1.scatter([.50, .50], [charge, discharge], color=[C_CHG, C_DIS], zorder=3)
ax1.annotate(f"刚停充电 {charge:.3f} V", (.50, charge), (.60, charge+.018), fontsize=8.8,
             arrowprops=dict(arrowstyle="->", color=C_CHG))
ax1.annotate(f"刚停放电 {discharge:.3f} V", (.50, discharge), (.60, discharge-.030), fontsize=8.8,
             arrowprops=dict(arrowstyle="->", color=C_DIS))
ax1.set(xlabel="SOC (0–1)", ylabel="OCV (V)", title="同一 SOC 的 OCV 受温度与充放方向影响")
ax1.legend(loc="lower right")

info = [observation_information(soc, 0.005**2) for soc in socs]
ax2.semilogy(socs, info, color=C_OK, lw=2, label="H²/R（σV=5 mV）")
for soc, label, xytext in [(0.05, "5%：H≈3.0", (.15, 2e5)), (.50, "50%：H≈0.1", (.58, 800)), (.95, "95%：H≈1.1", (.70, 5e4))]:
    value = observation_information(soc, .005**2)
    ax2.scatter([soc], [value], color=C_DIS, zorder=3)
    ax2.annotate(f"{label}\nH²/R={value:.0f}", (soc, value), xytext, fontsize=8.5,
                 arrowprops=dict(arrowstyle="->", color=C_DIS))
ax2.axvspan(.30, .80, color=C_GRID, alpha=.15, label="LFP 平台区")
ax2.set(xlabel="SOC (0–1)", ylabel="局部信息量 H²/R", title="平台区信息量低，不宜仅凭一次电压上调能力")
ax2.legend(loc="lower left")

save(fig, "ocv_decision_map", title="OCV 校准决策：温度、方向和信息量共同决定电压能否修正 SOC")
# @AI_GENERATED: end