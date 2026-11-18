# @AI_GENERATED
"""第12章 开环安时积分漂移对照：img/coulomb_drift.png（复用 ch05 统一数据）。
双栏：左 SOC 轨迹对比，右误差分解（初值常数 + 零漂斜坡 vs EKF 收敛）。
"""
from _figstyle import plt, save, C_OK, C_DIS, C_CHG, C_GRID, C_LIMIT
import ch05_production_ekf as m

true_soc, coulomb_soc, ekf_soc = m.run(seed=17)
steps = list(range(len(true_soc)))
last = steps[-1]
n = len(true_soc)

coulomb_error = [c - t for c, t in zip(coulomb_soc, true_soc)]
ekf_error = [e - t for e, t in zip(ekf_soc, true_soc)]
init_err = coulomb_soc[0] - true_soc[0]
drift_err = [ce - init_err for ce in coulomb_error]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 5))

# ── 左栏：SOC 轨迹对比 ─────────────────────────────────────────
ax1.plot(steps, true_soc, color=C_OK, lw=2.2, label="真值 SOC")
ax1.plot(steps, coulomb_soc, color=C_DIS, lw=1.8, ls="--",
         label="开环安时积分（初值 +20%，零漂 +0.5 A）")
ax1.plot(steps, ekf_soc, color=C_CHG, lw=1.6, label="带电压反馈（EKF）对照")
ax1.axhline(0.70, color=C_GRID, lw=0.9, ls=":")
ax1.annotate("错误初值 0.70", (0, 0.70), (130, 0.735),
             color=C_GRID, fontsize=8.5,
             arrowprops=dict(arrowstyle="->", color=C_GRID))
ax1.annotate(f"开环末端误差 {coulomb_error[-1]:+.3f}",
             (last, coulomb_soc[-1]),
             (max(0, last - 800), coulomb_soc[-1] + 0.06),
             color=C_DIS, fontsize=8.5,
             arrowprops=dict(arrowstyle="->", color=C_DIS))
ax1.annotate(f"EKF 末端误差 {ekf_error[-1]:+.3f}",
             (last, ekf_soc[-1]),
             (max(0, last - 800), ekf_soc[-1] + 0.04),
             color=C_CHG, fontsize=8.5,
             arrowprops=dict(arrowstyle="->", color=C_CHG))
ax1.set_xlabel("时间步 (s)")
ax1.set_ylabel("SOC (0–1)")
ax1.set_title("SOC 轨迹：开环漂移 vs EKF 收敛")
ax1.legend(loc="center right", fontsize=7.8)

# ── 右栏：误差分解 ─────────────────────────────────────────────
ax2.fill_between(steps, 0, [init_err] * n, color=C_GRID, alpha=0.25,
                 label=f"初值误差（恒定 {init_err:.2f}）")
ax2.plot(steps, drift_err, color=C_DIS, lw=2.0,
         label="零漂累积（+0.5 A 斜坡）")
ax2.plot(steps, coulomb_error, color=C_LIMIT, lw=2.2,
         label=f"开环总误差 = 初值 + 零漂")
ax2.plot(steps, ekf_error, color=C_CHG, lw=1.8,
         label="EKF 误差（趋于 0）")
ax2.axhline(0, color=C_GRID, lw=0.8, ls=":")
ax2.axhline(init_err, color=C_GRID, lw=0.7, ls=":")

drift_end = drift_err[-1]
ax2.annotate(f"初值 {init_err:.3f}（恒定不衰减）",
             (n // 4, init_err), (n // 4, init_err + 0.015),
             fontsize=8.5, color=C_GRID,
             arrowprops=dict(arrowstyle="->", color=C_GRID))
ax2.annotate(f"零漂末端 {drift_end:+.3f}",
             (last, drift_end),
             (max(0, last - 650), drift_end - 0.04),
             fontsize=8.5, color=C_DIS,
             arrowprops=dict(arrowstyle="->", color=C_DIS))
ax2.annotate(f"总误差 {coulomb_error[-1]:+.3f}",
             (last, coulomb_error[-1]),
             (max(0, last - 650), coulomb_error[-1] + 0.025),
             fontsize=8.5, color=C_LIMIT,
             arrowprops=dict(arrowstyle="->", color=C_LIMIT))
ax2.annotate(f"EKF {ekf_error[-1]:+.3f}",
             (last, ekf_error[-1]),
             (max(0, last - 650), ekf_error[-1] + 0.03),
             fontsize=8.5, color=C_CHG,
             arrowprops=dict(arrowstyle="->", color=C_CHG))
ax2.set_xlabel("时间步 (s)")
ax2.set_ylabel("SOC 误差 (0–1)")
ax2.set_title("误差分解：初值固化 + 零漂增长 vs EKF 自愈")
ax2.legend(loc="upper left", fontsize=7.5)

save(fig, "coulomb_drift",
     title="开环安时积分漂移 = 初值误差（恒定）+ 电流零漂（斜坡），EKF 用电压反馈将二者都收敛")
# @AI_GENERATED: end