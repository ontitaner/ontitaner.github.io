# @AI_GENERATED
"""第12章 开环安时积分漂移对照 img/coulomb_drift.png（复用 ch05 统一数据）。"""
from _figstyle import plt, save, C_OK, C_DIS, C_CHG, C_GRID
import ch05_production_ekf as m

true_soc, coulomb_soc, ekf_soc = m.run(seed=17)
steps = list(range(len(true_soc)))
last = steps[-1]

fig, ax = plt.subplots(figsize=(9, 4.6))
ax.plot(steps, true_soc, color=C_OK, lw=2.2, label="真值 SOC")
ax.plot(steps, coulomb_soc, color=C_DIS, lw=1.8, ls="--",
        label="开环安时积分（初值 +20%，零漂 +0.5 A）")
ax.plot(steps, ekf_soc, color=C_CHG, lw=1.6, label="带电压反馈（EKF）对照")
ax.axhline(0.70, color=C_GRID, lw=0.9, ls=":")
ax.annotate("错误初值 0.70", (0, 0.70), (130, 0.725),
            color=C_GRID, fontsize=9, arrowprops=dict(arrowstyle="->", color=C_GRID))
ax.annotate(f"开环末端误差 {coulomb_soc[-1]-true_soc[-1]:+.3f}\n初值误差永不消除",
            (last, coulomb_soc[-1]), (max(0, last-760), 0.63), color=C_DIS, fontsize=9,
            arrowprops=dict(arrowstyle="->", color=C_DIS))
ax.set_xlabel("时间步 (s)")
ax.set_ylabel("SOC (0–1)")
ax.legend(loc="center right")
save(fig, "coulomb_drift",
     title="开环安时积分无法自愈：初值误差恒定留存、电流零漂持续累积")
# @AI_GENERATED: end