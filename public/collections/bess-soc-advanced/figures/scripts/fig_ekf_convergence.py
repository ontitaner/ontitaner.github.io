# @AI_GENERATED
"""生成 ch04 EKF 收敛图 img/ekf_convergence.png。数据取自 lab/ch04 run()。"""
from _figstyle import plt, save
import ch04_ekf_vs_baseline as m

t, b, e = m.run()
ks = list(range(len(t)))

fig, ax = plt.subplots(figsize=(7, 4.2))
ax.plot(ks, t, color="#2ca02c", lw=2, label="真值 SOC")
ax.plot(ks, b, color="#d62728", lw=1.3, ls="--", label="安时积分基线（电流零漂 +0.5A）")
ax.plot(ks, e, color="#1f77b4", lw=1.5, label="EKF 估计")
ax.axhline(0.70, color="gray", lw=0.8, ls=":", alpha=.7)
ax.annotate("错误初值 0.70（+20%）", (0, 0.70), (120, 0.73), fontsize=9,
            arrowprops=dict(arrowstyle="->", color="gray"))
ax.annotate(f"EKF 收敛后残差≈{e[-1]-t[-1]:+.3f}\n（平台区可观测性弱）",
            (1799, e[-1]), (1200, 0.60), fontsize=9,
            arrowprops=dict(arrowstyle="->", color="#1f77b4"))
ax.annotate(f"基线持续发散 {b[-1]-t[-1]:+.2f}", (1799, b[-1]), (1100, 0.665), fontsize=9,
            arrowprops=dict(arrowstyle="->", color="#d62728"))
ax.set_xlabel("时间步 (s)")
ax.set_ylabel("SOC")
ax.set_title("ch04 EKF 从错误初值收敛 vs 安时积分基线发散")
ax.legend(loc="upper right")
save(fig, "ekf_convergence.png")
# @AI_GENERATED: end
