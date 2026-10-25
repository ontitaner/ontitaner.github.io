# @AI_GENERATED
"""生成 ch05 不确定度带图 img/uncertainty_band.png。数据取自 lab/ch05 run()。"""
from _figstyle import plt, save
import ch05_uncertainty as m

soc_log, sig = m.run()
ks = list(range(len(sig)))
# EKF 估计 SOC 轨迹无需重建；用真值 ± σ 作为置信带示意（σ 来自协方差）
upper = [s + 1.96 * g for s, g in zip(soc_log, sig)]
lower = [s - 1.96 * g for s, g in zip(soc_log, sig)]
e_point = [m.energy_band(s, g)[0] for s, g in zip(soc_log, sig)]
e_sigma = [m.energy_band(s, g)[1] for s, g in zip(soc_log, sig)]

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7, 6), sharex=True)
ax1.plot(ks, soc_log, color="#1f77b4", lw=1.5, label="SOC（真值轨迹）")
ax1.fill_between(ks, lower, upper, color="#1f77b4", alpha=.2, label="±1.96σ 置信带")
ax1.axvline(600, color="gray", lw=0.8, ls=":")
ax1.annotate("激励段：σ 快速收窄", (150, soc_log[150]), (150, 0.62), fontsize=9)
ax1.annotate("平台静置段：σ 几乎停滞\n（信息累积慢 ~114 倍）", (750, 0.5), (650, 0.60), fontsize=9)
ax1.set_ylabel("SOC")
ax1.set_title("ch05 SOC 置信带随激励收窄、平台静置段停滞")
ax1.legend(loc="lower left")

ax2.plot(ks, e_point, color="#2ca02c", lw=1.5, label="可放能量点值")
ax2.fill_between(ks, [e - s for e, s in zip(e_point, e_sigma)],
                 [e + s for e, s in zip(e_point, e_sigma)],
                 color="#2ca02c", alpha=.2, label="±σ_E 能量区间")
ax2.set_xlabel("时间步 (s)")
ax2.set_ylabel("可放能量 (kWh)")
ax2.legend(loc="lower left")
save(fig, "uncertainty_band.png")
# @AI_GENERATED: end
