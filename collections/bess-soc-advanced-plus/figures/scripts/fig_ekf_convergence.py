# @AI_GENERATED
"""第13章 EKF 收敛图：img/ekf_convergence.png。"""
from _figstyle import plt, save, C_OK, C_DIS, C_CHG, C_GRID
import ch05_production_ekf as m

true_soc, baseline_soc, ekf_soc = m.run(seed=17)
steps = list(range(len(true_soc)))
last = steps[-1]

fig, ax = plt.subplots(figsize=(9, 4.6))
ax.plot(steps, true_soc, color=C_OK, lw=2.2, label="统一模型真值 SOC")
ax.plot(steps, baseline_soc, color=C_DIS, lw=1.6, ls="--", label="安时积分（电流零漂 +0.5 A）")
ax.plot(steps, ekf_soc, color=C_CHG, lw=1.7, label="三状态 EKF")
ax.axhline(.70, color=C_GRID, lw=.8, ls=":")
ax.set_ylim(0.46, 0.76)
ax.annotate("错误初值 0.70（+20%）", (0, .70), (150, .735), fontsize=9,
            color=C_GRID, arrowprops=dict(arrowstyle="->", color=C_GRID))
ax.annotate(f"EKF 末端误差 {ekf_soc[-1] - true_soc[-1]:+.3f}",
            (last, ekf_soc[-1]), (max(0, last - 560), .565), fontsize=9,
            color=C_CHG, arrowprops=dict(arrowstyle="->", color=C_CHG))
ax.annotate(f"安时积分末端误差 {baseline_soc[-1] - true_soc[-1]:+.3f}",
            (last, baseline_soc[-1]), (max(0, last - 640), .655), fontsize=9,
            color=C_DIS, arrowprops=dict(arrowstyle="->", color=C_DIS))
ax.set_xlabel("时间步 (s)")
ax.set_ylabel("SOC (0–1)")
ax.legend(loc="lower center", ncol=3)
save(fig, "ekf_convergence",
     title="EKF 用电压反馈从错误初值收敛，安时积分保留初值与零漂误差")
# @AI_GENERATED: end