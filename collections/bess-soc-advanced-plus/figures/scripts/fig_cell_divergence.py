# @AI_GENERATED
"""第19章 木桶效应与可解释异常评分：img/cell_divergence.png。"""
from _figstyle import plt, save, C_CHG, C_DIS, C_OK, C_ACC, C_GRID, C_LIMIT
import ch08_group_anomaly as m

socs = list(m.PACK_SOC0)
trajectory = [list(socs)]
while min(socs) > m.SOC_MIN + 1e-9:
    socs = [soc - m.P_EACH_KW * m.DT_H / m.CLUSTER_NOMINAL_ENERGY_KWH for soc in socs]
    trajectory.append(list(socs))
times_h = [index * m.DT_H for index in range(len(trajectory))]

observations = m.teaching_observations()
scores = [m.score_observation(item.socs).scores[3] for item in observations[:-1]]
score_times = [item.sample.device_time_s / 60.0 for item in observations[:-1]]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.5, 4.2))
cluster_colors = [C_CHG, C_OK, C_ACC, C_DIS]
for cluster in range(len(m.PACK_SOC0)):
    ax1.plot(times_h, [row[cluster] for row in trajectory], color=cluster_colors[cluster],
             lw=1.6, label=f"簇{cluster + 1} 初始 {m.PACK_SOC0[cluster]:.0%}")
ax1.axhline(m.SOC_MIN, color=C_LIMIT, lw=1.2, ls="--", label=f"放电下限 {m.SOC_MIN:.0%}")
ax1.set(xlabel="放电时间 (h)", ylabel="簇级 SOC", title="最低簇先触下限，决定可用能力")
ax1.legend(fontsize=8, ncol=2)

ax2.plot(score_times, scores, marker="o", color=C_DIS, lw=1.6, label="簇4 鲁棒评分")
ax2.axhline(m.SCORE_THRESHOLD, color=C_GRID, lw=1.2, ls="--",
            label=f"事件阈值 {m.SCORE_THRESHOLD:.0f}")
ax2.annotate(f"连续两帧越限(评分 {scores[-1]:.1f})\n→ 开异常事件 GA-002-C4",
             (score_times[-1], scores[-1]), (score_times[0] + 0.3, scores[-1] - 2.5),
             fontsize=8.5, arrowprops=dict(arrowstyle="->", color=C_DIS))
ax2.set(xlabel="采样时间 (min)", ylabel="无量纲异常评分", title="评分可解释且抑制单点噪声")
ax2.legend(fontsize=8.5)
save(fig, "cell_divergence", title="木桶效应与可解释异常评分")
# @AI_GENERATED: end